"""Pure/mocked boundary cases only. NEVER invokes an extraction executable."""
import asyncio
import json
from pathlib import Path, PurePosixPath
import signal
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from services.backend import mpv_inspector as subject


def record(**values):
    return subject.PREFIX + json.dumps(values).encode() + b'\n'


class ParserBoundaries(unittest.TestCase):
    def test_no_fake_values_and_tag_urls_paths_not_returned(self):
        value = subject.parse_metadata(record(duration_s=72.5, title='Real\u202etitle', artist='https://example.org', album='/private/path', tracks=[{'type': 'video', 'albumart': True, 'external-filename': '/private'}]))
        self.assertEqual(value, {'duration_s': 72.5, 'title': 'Realtitle', 'artist': None, 'album': None, 'tracks': [{'type': 'video', 'albumart': True}]})
        self.assertIsNone(subject.parse_metadata(b'not metadata'))

    def test_nonfinite_huge_bool_and_unhashable_track_fields(self):
        for value in [True, float('nan'), float('inf'), -1, 0, 10**400]:
            result = subject.parse_metadata(record(duration_s=value, tracks=[{'type': {}}]))
            self.assertIsNone(result['duration_s'])
            self.assertEqual(result['tracks'], [])

    def test_output_and_duplicate_record_caps(self):
        self.assertIsNone(subject.parse_metadata(b'x' * (subject.MAX_STDOUT + 1)))
        self.assertIsNone(subject.parse_metadata(record(title='One') + record(title='Two')))
        result = subject.parse_metadata(record(title='A' * 300, tracks=[{'type': 'audio'}] * 40))
        self.assertEqual(len(result['title']), 240)
        self.assertEqual(len(result['tracks']), 16)

    def test_fixed_argument_surface(self):
        args = subject.build_argv(PurePosixPath('/usr/bin/mpv'), PurePosixPath('/app/inspect.lua'), 17, PurePosixPath('/private/owned-job'))
        self.assertEqual(args[-2:], ['--', 'fd://17'])
        self.assertIn('--ao=null', args)
        self.assertIn('--load-scripts=no', args)
        self.assertIn('--script=/app/inspect.lua', args)
        self.assertIn('--access-references=no', args)
        self.assertIn('--autoload-files=no', args)
        self.assertIn('--demuxer-lavf-o=protocol_whitelist=pipe', args)
        self.assertEqual(len([a for a in args if a.startswith('--script=')]), 1)
        self.assertFalse(any('input-ipc' in a for a in args))
        self.assertIn('RLIMIT_FSIZE', subject.LAUNCHER)
        self.assertIn('os.nice(10)', subject.LAUNCHER)

    def test_jpeg_header_limits_without_claiming_decode(self):
        # Synthetic header for parser coverage only, never a product poster.
        small = b'\xff\xd8\xff\xc0\x00\x08\x08\x00\xb4\x01\x40\x03\xff\xd9'
        self.assertEqual(subject.jpeg_dimensions(small), (320, 180))
        self.assertIsNone(subject.jpeg_dimensions(small.replace(b'\x01\x40', b'\x01\x41')))
        self.assertIsNone(subject.jpeg_dimensions(small[:-2]))
        self.assertIsNone(subject.jpeg_dimensions(b'x' * (subject.MAX_JPEG + 1)))


class AsyncBoundaries(unittest.IsolatedAsyncioTestCase):
    async def test_stream_cap_kills_before_unbounded_accumulation(self):
        stream = asyncio.StreamReader()
        stream.feed_data(b'a' * 1025)
        stream.feed_eof()
        with self.assertRaises(subject.InspectionLimit):
            await subject._bounded_read(stream, 1024)

    async def test_success_uses_only_passed_fd_and_new_owned_session(self):
        process = type('Fake', (), {})()
        process.stdout, process.stderr = asyncio.StreamReader(), asyncio.StreamReader()
        process.stdout.feed_data(record(duration_s=3))
        process.stdout.feed_eof()
        process.stderr.feed_eof()
        process.returncode = 0
        process.wait = AsyncMock(return_value=0)
        with tempfile.TemporaryDirectory() as folder, patch.object(subject.asyncio, 'create_subprocess_exec', AsyncMock(return_value=process)) as spawn:
            raw, code = await subject._run(['fixed-trusted-command'], 17, Path(folder))
        self.assertEqual(code, 0)
        self.assertEqual(subject.parse_metadata(raw)['duration_s'], 3)
        self.assertEqual(spawn.call_args.kwargs['pass_fds'], (17,))
        self.assertTrue(spawn.call_args.kwargs['start_new_session'])
        self.assertNotIn('preexec_fn', spawn.call_args.kwargs)
        self.assertEqual(spawn.call_args.kwargs['stdin'], asyncio.subprocess.DEVNULL)

    async def test_timeout_and_cancel_kill_exact_owned_group_and_reap(self):
        for cancel in [False, True]:
            with self.subTest(cancel=cancel):
                stopped = asyncio.Event()
                process = type('Fake', (), {})()
                process.pid, process.returncode = 234567, None
                process.stdout, process.stderr = asyncio.StreamReader(), asyncio.StreamReader()
                async def ended():
                    await stopped.wait()
                    process.returncode = -9
                    return -9
                process.wait = ended
                def kill(pid, sig):
                    self.assertEqual((pid, sig), (process.pid, 9))
                    process.stdout.feed_eof()
                    process.stderr.feed_eof()
                    stopped.set()
                with tempfile.TemporaryDirectory() as folder, patch.object(subject.asyncio, 'create_subprocess_exec', AsyncMock(return_value=process)), patch.object(subject.os, 'killpg', kill, create=True), patch.object(subject.signal, 'SIGKILL', 9, create=True), patch.object(subject, 'TIMEOUT_S', .02):
                    task = asyncio.create_task(subject._run(['fixed'], 17, Path(folder)))
                    if cancel:
                        await asyncio.sleep(.005)
                        task.cancel()
                    with self.assertRaises(asyncio.CancelledError if cancel else TimeoutError):
                        await task
                self.assertTrue(stopped.is_set())
                self.assertEqual(process.returncode, -9)

    async def test_cancel_while_spawn_pending_still_reaps_owned_process(self):
        stopped = asyncio.Event()
        process = type('Fake', (), {})()
        process.pid, process.returncode = 234568, None
        process.stdout, process.stderr = asyncio.StreamReader(), asyncio.StreamReader()
        async def wait():
            await stopped.wait()
            process.returncode = -9
            return -9
        process.wait = wait
        async def spawn(*args, **kwargs):
            await asyncio.sleep(.02)
            return process
        def kill(pid, sig):
            self.assertEqual((pid, sig), (process.pid, 9))
            stopped.set()
        with tempfile.TemporaryDirectory() as folder, patch.object(subject.asyncio, 'create_subprocess_exec', spawn), patch.object(subject.os, 'killpg', kill, create=True), patch.object(subject.signal, 'SIGKILL', 9, create=True):
            task = asyncio.create_task(subject._run(['fixed'], 17, Path(folder)))
            await asyncio.sleep(.001)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(process.returncode, -9)

    async def test_supervisor_output_flood_kills_and_reaps(self):
        stopped = asyncio.Event()
        process = type('Fake', (), {})()
        process.pid, process.returncode = 234569, None
        process.stdout, process.stderr = asyncio.StreamReader(), asyncio.StreamReader()
        process.stdout.feed_data(b'x' * (subject.MAX_STDOUT + 1))
        async def wait():
            await stopped.wait()
            process.returncode = -9
            return -9
        process.wait = wait
        def kill(pid, sig):
            self.assertEqual((pid, sig), (process.pid, 9))
            stopped.set()
        with tempfile.TemporaryDirectory() as folder, patch.object(subject.asyncio, 'create_subprocess_exec', AsyncMock(return_value=process)), patch.object(subject.os, 'killpg', kill, create=True), patch.object(subject.signal, 'SIGKILL', 9, create=True):
            with self.assertRaises(subject.InspectionLimit):
                await subject._run(['fixed'], 17, Path(folder))
        self.assertEqual(process.returncode, -9)


if __name__ == '__main__':
    unittest.main()
