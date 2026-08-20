import asyncio
import logging
import sys
from gan_cube import GanCubeClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    cube = GanCubeClient()
    
    def on_event(event):
        if event["type"] == "MOVE":
            print(f"Move detected: {event['move']}")
        elif event["type"] == "FACELETS":
            print(f"Cube state: {event['facelets']}")
        elif event["type"] == "BATTERY":
            print(f"Battery level: {event['batteryLevel']}%")
        elif event["type"] == "HARDWARE":
            print(f"Hardware info: {event}")
        else:
            print(f"Event: {event['type']}")

    cube.set_on_event(on_event)
    
    try:
        await cube.connect()
        print("Connected to GAN Cube! Try making some moves...")
        
        # Keep the script running to receive notifications
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
