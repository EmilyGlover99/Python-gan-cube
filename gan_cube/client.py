import asyncio
import logging
from bleak import BleakClient, BleakScanner
from .definitions import *
from .encrypter import GanGen2CubeEncrypter
from .protocol import GanGen2ProtocolDriver

logger = logging.getLogger(__name__)

class GanCubeClient:
    def __init__(self, address=None, name=None):
        self.address = address
        self.name = name
        self.client = None
        self.encrypter = None
        self.driver = GanGen2ProtocolDriver()
        self._on_event = None

    def set_on_event(self, callback):
        self._on_event = callback

    async def connect(self):
        if not self.address:
            logger.info("Scanning for GAN Cube...")
            devices = await BleakScanner.discover()
            for d in devices:
                if d.name and (d.name.startswith("GAN") or d.name.startswith("MG") or d.name.startswith("AiCube")):
                    self.address = d.address
                    self.name = d.name
                    break
        
        if not self.address:
            raise Exception("GAN Cube not found")

        logger.info(f"Connecting to {self.name} ({self.address})...")
        self.client = BleakClient(self.address)
        await self.client.connect()

        # For GAN cubes, we need the MAC address for the encryption salt.
        # On Windows, bleak address is the MAC. On macOS it's a UUID.
        # The JS library extracts it from manufacturer data.
        # Let's assume for now the address we have is usable or we might need to fix it.
        mac_str = self.address.replace(":", "").replace("-", "")
        if len(mac_str) > 12: # Handle UUIDs by taking last 12 chars if it looks like one? 
             # Actually GAN MAC is in manufacturer data.
             pass
        
        # Simplified salt creation: reverse MAC bytes
        # This part might need adjustment depending on how bleak returns the address
        mac_bytes = bytes.fromhex(mac_str[-12:])
        salt = list(mac_bytes)[::-1]
        
        key = GAN_ENCRYPTION_KEYS[0]
        if self.name and self.name.startswith("AiCube"):
            key = GAN_ENCRYPTION_KEYS[1]
            
        self.encrypter = GanGen2CubeEncrypter(key["key"], key["iv"], salt)

        await self.client.start_notify(GAN_GEN2_STATE_CHARACTERISTIC, self._notification_handler)
        
        # Request initial state
        await self.send_command("REQUEST_FACELETS")
        await self.send_command("REQUEST_HARDWARE")

    async def send_command(self, command_type):
        msg = self.driver.create_command_message(command_type)
        if msg:
            encrypted_msg = self.encrypter.encrypt(msg)
            await self.client.write_gatt_char(GAN_GEN2_COMMAND_CHARACTERISTIC, encrypted_msg)

    def _notification_handler(self, sender, data):
        try:
            decrypted_data = self.encrypter.decrypt(bytes(data))
            events = self.driver.handle_state_event(decrypted_data)
            if self._on_event:
                for event in events:
                    self._on_event(event)
        except Exception as e:
            logger.error(f"Error in notification handler: {e}", exc_info=True)

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
