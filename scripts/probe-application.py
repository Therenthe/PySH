"""Read real device adapters without changing network or Bluetooth pairings."""
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.backend.device import Device
from services.backend.player import Player


async def main():
    device, player = Device(), Player()
    await device.initialize()
    try:
        await player.start()
        report = {
            "network": await device.network_status(),
            "bluetooth": await device.bluetooth_status(),
            "audio": await device.audio_status(),
            "player": await player.status(),
        }
        # Keep credentials, SSIDs, IP and MAC addresses out of shared evidence.
        for item in report["network"].get("devices", []):
            item.pop("ssid", None)
            item.pop("ip", None)
        report["network"].pop("connection", None)
        report["network"].pop("saved", None)
        for item in report["bluetooth"].get("devices", []):
            item.pop("address", None)
        print(json.dumps(report, indent=2))
    finally:
        await player.close()
        await device.close()


asyncio.run(main())
