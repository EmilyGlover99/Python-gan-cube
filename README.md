# Python GAN Cube Library

A Python library for interacting with GAN smart cubes over Bluetooth Low Energy (BLE). This library allows you to receive real-time move events and cube state updates from your GAN cube.

## Features

- **Automatic Scanning:** Continuously scans Bluetooth for known GAN cube addresses/manufacturer info until a cube is found.
- **Real-time Moves:** Receive move events (e.g., `U`, `R'`, `B` etc.) as they happen.
- **Cube State Tracking:** Automatically retrieves and updates the full cube state (facelets) after each move.
- **Encryption Support:** Handles the GAN Gen2 protocol encryption (compatible with GAN 356 i series, etc.).
- **macOS Compatible:** Corrected MAC address handling for macOS Bluetooth stack.

## Dependencies

- [bleak](https://github.com/hbldh/bleak): Bluetooth Low Energy platform support.
- [pycryptodome](https://pycryptodome.readthedocs.io/en/latest/): AES encryption for the GAN protocol.

You can install the dependencies using pip:

```bash
pip install bleak pycryptodome
```

## Usage

The following example shows how to connect to a cube and listen for events.

```python
import asyncio
import sys
from gan_cube import GanCubeClient

async def main():
    # Initialize the client
    cube = GanCubeClient()
    
    # Define an event handler
    def on_event(event):
        if event["type"] == "MOVE":
            print(f"Cube Moved: {event['move']}")
        elif event["type"] == "FACELETS":
            if "error" in event:
                print(f"Cube state error: {event['error']}")
            else:
                print(f"Cube State: {event['facelets']}")
        elif event["type"] == "BATTERY":
            print(f"Battery level: {event['batteryLevel']}%")
        elif event["type"] == "HARDWARE":
            print(f"Hardware info: {event}")

    cube.set_on_event(on_event)
    
    try:
        # This will scan continuously until a cube is found
        await cube.connect()
        print("Connected to GAN Cube! Try making some moves...")
        
        # Keep the script running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await cube.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
```

## Interpreting the Output

### Cube Moved
When you turn a face, the library emits a `MOVE` event:
`Cube Moved: U`
`Cube Moved: R'`

### Cube State
After every move, the library requests the full state of the cube. The `facelets` string is a 54-character string representing the colors of each facelet in Kociemba order (U, R, F, D, L, B).

Example:
`Cube State: UUFUUBUUBRRLRRLRRLFFUFFUBBUDDFDDFDDBLLLLLLRRRDBBDBBDFF`

Each character represents a face:
- `U`: Up (White)
- `R`: Right (Red)
- `F`: Front (Green)
- `D`: Down (Yellow)
- `L`: Left (Orange)
- `B`: Back (Blue)

## Troubleshooting

- **No Cube Found:** Ensure your GAN cube is awake (give it a few turns) and not connected to another device/app.
- **Invalid State:** If you see `Cube state error: INVALID_STATE`, it usually means there was a decryption error. The library attempts to extract the hardware MAC address from the advertisement to use as an encryption salt. Ensure your system allows Bluetooth scanning with manufacturer data access.

## Acknowledgments

Heavily based on the [gan-web-bluetooth](https://github.com/h-shina/gan-web-bluetooth) Javascript library.