"""

Read the bluetooth signals coming from the GANCube

"""
import argparse
import asyncio
import uuid
import sys

from bleak import BleakClient

DEFAULT_ADDRESS = 'FD6027D1-39BE-971F-3CA1-38CA3823D1A6'
tx_address = '28be4cb6-cd67-11e9-a32f-2a2ae2dbcce4'

def data_handler(sender: int, data: bytearray) -> None:
    """Simple notification handler which prints the data received."""
    # print(f"Notification from {sender}: {data.hex()}")

    # Prints raw integers, a hex string, and tries to decode as text
    print(f"\n--- New Data Received ---")
    print(f"Raw Byte List: {list(data)}")
    print(f"Hex String:    {data.hex()}")
    try:
        print(f"As Text string: {data.decode('utf-8').strip()}")
    except UnicodeDecodeError:
        print("As Text string: (Cannot decode as plain text)")

async def read_once(address: str) -> None:
    """Read the current sensor values from the GANCube device."""
    print(f"Waiting for signals from {address}...")

    async with BleakClient(address) as client:
        await client.start_notify(tx_address, data_handler)

        # Keep running for 20 seconds to collect data samples
        await asyncio.sleep(200.0)

        print("Stopping stream...")
        await client.stop_notify(tx_address)

async def get_services(address: str) -> None:
    """Read the current sensor values from the GANCube device."""
    print(f"Waiting for signals from {address}...")

    async with BleakClient(address) as client:
        # Iterate through all discovered services
        for service in client.services:
            print(f"\n[Service] {service.uuid} : {service.description}")

            # Iterate through all characteristics in each service
            for char in service.characteristics:
                print(f"  [Characteristic] {char.uuid} ({char.properties})")
                print(f"    Handle: {char.handle}, Description: {char.description}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="GANCube BLE reader")
    p.add_argument("--address", default=DEFAULT_ADDRESS, help="BLE address/UUID")
    p.add_argument("--service-scan", action="store_true" , help="Scan for services and characteristics (1 to enable)")
    return p

def __main__() -> int:
    args = build_parser().parse_args()
    if args.service_scan:
        asyncio.run(get_services(args.address))
    else:
        asyncio.run(read_once(args.address))
    return 0


if __name__ == "__main__":

    # sys.argv = ['cube.py', '--service-scan']
    raise SystemExit(__main__())