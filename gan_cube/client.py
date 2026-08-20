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
            devices = await BleakScanner.discover(return_adv=True)
            for d, adv in devices.values():
                if d.name and (d.name.startswith("GAN") or d.name.startswith("MG") or d.name.startswith("AiCube")):
                    self.address = d.address
                    self.name = d.name
                    
                    # Extract MAC from manufacturer data
                    # GAN_CIC_LIST is a list of possible manufacturer IDs
                    for m_id in GAN_CIC_LIST:
                        if m_id in adv.manufacturer_data:
                            data = adv.manufacturer_data[m_id]
                            # JS extractMAC: dataView.buffer.slice(0, 9) then last 6 bytes reversed
                            # In bleak, data is bytes. We want the last 6 bytes of the first 9 bytes.
                            if len(data) >= 9:
                                # JS getManufacturerDataBytes takes slice(0, 9)
                                data_9 = data[:9]
                                # The JS code reads them from length-i, which is reverse order.
                                # dataView.getUint8(dataView.byteLength - i) where i=1..6
                                # If dataView is 9 bytes, it takes bytes 8, 7, 6, 5, 4, 3.
                                # JS extractMAC: M6:M5:M4:M3:M2:M1
                                mac_parts = []
                                for i in range(1, 7):
                                    mac_parts.append(format(data_9[9-i], '02X'))
                                self.mac = ":".join(mac_parts)
                                logger.info(f"Extracted MAC address from advertisement: {self.mac}")
                                break
                    break
        
        if not self.address:
            raise Exception("GAN Cube not found")

        logger.info(f"Connecting to {self.name} ({self.address})...")
        self.client = BleakClient(self.address)
        await self.client.connect()

        # Create encryption salt from MAC address bytes placed in reverse order
        if hasattr(self, 'mac'):
            # self.mac is "M6:M5:M4:M3:M2:M1"
            mac_parts = self.mac.split(":")
            # salt = [M1, M2, M3, M4, M5, M6]
            salt = [int(x, 16) for x in reversed(mac_parts)]
        else:
            # Fallback to address if MAC extraction failed (e.g. not in advertisement)
            # Bleak address on macOS is UUID, on others it might be MAC.
            # If it's a MAC string "M1:M2:M3:M4:M5:M6", salt should be [M6, M5, M4, M3, M2, M1]
            mac_str = self.address.replace(":", "").replace("-", "")
            if len(mac_str) > 12:
                mac_str = mac_str[-12:]
            mac_bytes = bytes.fromhex(mac_str)
            salt = list(mac_bytes)[::-1]
        
        logger.info(f"Using salt: {[format(x, '02X') for x in salt]}")
        
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
            # logger.info(f"Notification data: {bytes(data).hex()}")
            decrypted_data = self.encrypter.decrypt(bytes(data))
            # logger.info(f"Decrypted data: {decrypted_data.hex()}")
            events = self.driver.handle_state_event(decrypted_data)
            if self._on_event:
                for event in events:
                    self._on_event(event)
        except Exception as e:
            logger.error(f"Error in notification handler: {e}", exc_info=True)

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
