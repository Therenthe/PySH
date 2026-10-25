"""Private synthetic files and pure/mocked boundaries; no real user media."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from services.backend.content import _write_json_atomic
from services.backend import watch_history as subject


class Clock:
    mono = 1000
    wall = 2000
    def monotonic(self): return self.mono
    def timestamp(self): return self.wall


class WatchBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.path = self.base / 'history.json'
        self.clock = Clock()
        self.approved = {}
        self.files = []
        self.fail_write = False
        self.readonly = patch.object(subject, '_readonly', return_value=True)
        self.readonly.start()  # Windows mock; actual fixture FDs are O_RDONLY.
        def writer(path, value):
            if self.fail_write: raise OSError('synthetic atomic write failure')
            _write_json_atomic(path, value)
        self.writer = writer
        self.h = self.open_history()

    def tearDown(self):
        self.h.shutdown()
        for fd in self.files: os.close(fd)
        self.readonly.stop()
        self.temp.cleanup()

    def open_history(self):
        return subject.WatchHistory(self.path, validate=lambda p, i: self.approved.get(p) == i,
                    writer=self.writer, monotonic=self.clock.monotonic, wall=self.clock.timestamp)

    def fixture(self, name='fixture.mp4', identity='opaque_A'):
        p = self.base / name
        p.write_bytes(b'not decoded: synthetic test fixture')
        fd = os.open(p, os.O_RDONLY)
        self.files.append(fd)
        canonical = str(p.resolve())
        self.approved[canonical] = identity
        return canonical, fd, identity

    def start(self, fixture=None):
        return self.h.start(*(fixture or self.fixture()))['session_id']

    def assertClosed(self, fd):
        with self.assertRaises(OSError): os.fstat(fd)

    def test_progress_strict_finite_and_stale_sequences(self):
        token = self.start()
        for position, duration in [(True, 100), (20, True), (float('nan'), 100), (20, float('inf')), (-1, 100), (120, 100), ('20', 100), (10**400, 100), (20, 0)]:
            with self.subTest(position=type(position).__name__, duration=type(duration).__name__):
                with self.assertRaises(subject.WatchError): self.h.update(token, 0, position, duration)
        self.assertEqual(self.h.active.sequence, -1)
        self.h.update(token, 0, 20, 100)
        for seq in [0, -1, True, 1.2, subject.MAX_SEQUENCE + 1]:
            with self.assertRaises(subject.WatchError): self.h.update(token, seq, 30, 100)
        self.assertEqual(self.h.continuing()[0]['position_s'], 20)

    def test_under_ten_near_end_and_ended_remove_without_resurrection(self):
        token = self.start()
        self.h.update(token, 0, 9.9, 100)
        self.assertEqual(self.h.continuing(), [])
        self.h.update(token, 1, 10, 100)
        self.assertEqual(len(self.h.continuing()), 1)
        self.h.update(token, 2, 95, 100)
        self.assertEqual(self.h.continuing(), [])
        self.h.update(token, 3, 20, 100)
        self.h.update(token, 4, 100, 100, ended=True)
        self.h.update(token, 5, 40, 100)  # late timeupdate after ended
        self.assertEqual(self.h.continuing(), [])

    def test_clear_disables_current_session_late_updates_but_not_new_start(self):
        fixture = self.fixture()
        token = self.start(fixture)
        self.h.update(token, 0, 25, 100)
        self.h.clear(fixture[2])
        self.h.update(token, 1, 35, 100, final=True)
        self.assertEqual(self.h.continuing(), [])
        new = self.start(fixture)
        self.h.update(new, 0, 40, 100)
        self.assertEqual(self.h.continuing()[0]['position_s'], 40)

    def test_expiry_paused_heartbeat_closes_duplicate_only(self):
        fixture = self.fixture()
        token = self.start(fixture)
        duplicate = self.h.active.fd
        info = os.fstat(fixture[1])
        self.assertTrue(self.h.in_use(info.st_dev, info.st_ino))
        self.clock.mono += 119
        self.h.heartbeat(token, 0)
        self.clock.mono += 119
        self.assertTrue(self.h.in_use(info.st_dev, info.st_ino))
        self.clock.mono += 1
        self.assertTrue(self.h.expire())
        self.assertClosed(duplicate)
        self.assertIsNotNone(os.fstat(fixture[1]))
        with self.assertRaises(subject.WatchError): self.h.update(token, 1, 20, 100)

    def test_replacement_rejects_stale_session_and_preserves_caller_offset(self):
        first = self.fixture()
        os.lseek(first[1], 7, os.SEEK_SET)
        old = self.start(first)
        old_duplicate = self.h.active.fd
        new = self.start(self.fixture('second.mp4', 'opaque_B'))
        self.assertClosed(old_duplicate)
        self.assertFalse(self.h.close(old))
        with self.assertRaises(subject.WatchError): self.h.update(old, 0, 20, 100)
        self.assertEqual(os.lseek(first[1], 0, os.SEEK_CUR), 7)
        self.assertTrue(self.h.close(new))

    def test_final_update_and_close_commit_together_failed_write_preserves_state(self):
        token = self.start()
        self.h.update(token, 0, 20, 100)
        old_disk = self.path.read_bytes()
        duplicate = self.h.active.fd
        self.fail_write = True
        with self.assertRaises(subject.WatchError): self.h.update(token, 1, 30, 100, final=True)
        self.assertEqual(self.h.active.sequence, 0)
        self.assertEqual(self.path.read_bytes(), old_disk)
        self.assertEqual(self.h.continuing()[0]['position_s'], 20)
        self.assertIsNotNone(os.fstat(duplicate))
        self.fail_write = False
        self.h.update(token, 1, 30, 100, final=True)
        self.assertIsNone(self.h.active)
        self.assertClosed(duplicate)
        self.assertEqual(self.open_history().continuing()[0]['position_s'], 30)

    def test_failed_clear_is_not_silently_confirmed(self):
        token = self.start()
        self.h.update(token, 0, 20, 100)
        self.fail_write = True
        with self.assertRaises(subject.WatchError): self.h.clear('opaque_A')
        self.assertTrue(self.h.active.history_enabled)
        self.assertEqual(len(self.h.continuing()), 1)

    def test_stat_change_or_confinement_change_invalidates_active(self):
        fixture = self.fixture()
        token = self.start(fixture)
        duplicate = self.h.active.fd
        Path(fixture[0]).write_bytes(b'changed synthetic contents')
        with self.assertRaises(subject.WatchError): self.h.heartbeat(token, 0)
        self.assertClosed(duplicate)
        token = self.start(fixture)
        self.approved.clear()
        with self.assertRaises(subject.WatchError): self.h.heartbeat(token, 0)

    def test_unmounted_hidden_without_erasing_and_newest_twelve(self):
        for i in range(15):
            f = self.fixture(f'fixture_{i}.mp4', f'opaque_{i}')
            token = self.start(f)
            self.clock.wall += 1
            self.h.update(token, 0, 20, 100, final=True)
        self.assertEqual(len(self.h.continuing()), 12)
        self.assertEqual(self.h.continuing()[0]['identity'], 'opaque_14')
        saved = self.path.read_bytes()
        approved = dict(self.approved)
        self.approved.clear()
        self.assertEqual(self.h.continuing(), [])
        self.assertEqual(self.path.read_bytes(), saved)
        self.approved.update(approved)
        self.assertEqual(len(self.h.continuing()), 12)

    def test_history_cap_and_json_bound(self):
        for i in range(43):
            token = self.start(self.fixture(f'bounded_{i}.mp4', f'opaque_{i}'))
            self.clock.wall += 1
            self.h.update(token, 0, 20, 100, final=True)
        document = json.loads(self.path.read_text(encoding='utf8'))
        self.assertEqual(len(document['records']), 40)
        self.assertLessEqual(self.path.stat().st_size, subject.MAX_BYTES)
        self.assertNotIn('modified_ns', self.path.read_text(encoding='utf8'))
        self.assertNotIn('opaque_0', self.h.records)

    def test_corrupt_oversized_version_and_nonfinite_store_safe_empty(self):
        for raw in [b'{broken', b'x' * (subject.MAX_BYTES + 1), b'{"version":true,"records":[]}', b'{"version":1,"records":[{"unexpected":"field"}]}']:
            self.path.write_bytes(raw)
            self.assertEqual(self.open_history().records, {})
        token = self.start()
        self.h.update(token, 0, 20, 100, final=True)
        data = json.loads(self.path.read_text())
        data['records'][0]['duration_s'] = float('nan')
        self.path.write_text(json.dumps(data))
        self.assertEqual(self.open_history().records, {})

    def test_after_successful_unlink_best_effort_failure_still_invalidates_memory_session(self):
        fixture = self.fixture()
        token = self.start(fixture)
        self.h.update(token, 0, 20, 100)
        duplicate = self.h.active.fd
        self.fail_write = True
        # Synthetic post-unlink notification only: helper never unlinks anything.
        self.approved.clear()
        self.assertFalse(self.h.after_unlink(fixture[0], fixture[2]))
        self.assertEqual(self.h.continuing(), [])
        self.assertClosed(duplicate)
        with self.assertRaises(subject.WatchError): self.h.update(token, 1, 30, 100)
        self.assertTrue(Path(fixture[0]).exists())  # no delete authority

    def test_nonregular_fd_and_readwrite_fd_rejected_without_replacing_session(self):
        token = self.start()
        read, write = os.pipe()
        try:
            with self.assertRaises(subject.WatchError): self.h.start(str(self.base / 'pipe.mp4'), read, 'opaque_pipe')
        finally:
            os.close(read)
            os.close(write)
        with patch.object(subject, '_readonly', return_value=False):
            with self.assertRaises(subject.WatchError): self.h.start(*self.fixture('write.mp4', 'opaque_write'))
        self.assertEqual(self.h.active.token, token)


if __name__ == '__main__':
    unittest.main()
