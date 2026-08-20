import struct
from .utils import now, to_kociemba_facelets

class GanProtocolMessageView:
    def __init__(self, message: bytes):
        self.bits = "".join([format(byte, '08b') for byte in message])

    def get_bit_word(self, start_bit: int, bit_length: int, little_endian=False) -> int:
        if bit_length <= 8:
            return int(self.bits[start_bit:start_bit + bit_length], 2)
        elif bit_length == 16 or bit_length == 32:
            byte_length = bit_length // 8
            buf = bytearray()
            for i in range(byte_length):
                byte_val = int(self.bits[start_bit + 8 * i:start_bit + 8 * i + 8], 2)
                buf.append(byte_val)
            fmt = "<" if little_endian else ">"
            fmt += "H" if bit_length == 16 else "I"
            return struct.unpack(fmt, buf)[0]
        else:
            raise ValueError("Unsupported bit word length")

class GanGen2ProtocolDriver:
    def __init__(self):
        self.last_serial = -1
        self.last_move_timestamp = 0
        self.cube_timestamp = 0

    def create_command_message(self, command_type: str) -> bytes:
        msg = bytearray(20)
        if command_type == 'REQUEST_FACELETS':
            msg[0] = 0x04
        elif command_type == 'REQUEST_HARDWARE':
            msg[0] = 0x05
        elif command_type == 'REQUEST_BATTERY':
            msg[0] = 0x09
        elif command_type == 'REQUEST_RESET':
            msg[0:12] = [0x0A, 0x05, 0x39, 0x77, 0x00, 0x00, 0x01, 0x23, 0x45, 0x67, 0x89, 0xAB]
        else:
            return None
        return bytes(msg)

    def handle_state_event(self, event_message: bytes):
        timestamp = now()
        cube_events = []
        msg = GanProtocolMessageView(event_message)
        event_type = msg.get_bit_word(0, 4)

        if event_type == 0x01: # GYRO
            qw = msg.get_bit_word(4, 16)
            qx = msg.get_bit_word(20, 16)
            qy = msg.get_bit_word(36, 16)
            qz = msg.get_bit_word(52, 16)

            vx = msg.get_bit_word(68, 4)
            vy = msg.get_bit_word(72, 4)
            vz = msg.get_bit_word(76, 4)

            def parse_q(q):
                return (1 - (q >> 15) * 2) * (q & 0x7FFF) / 0x7FFF

            def parse_v(v):
                return (1 - (v >> 3) * 2) * (v & 0x7)

            cube_events.append({
                "type": "GYRO",
                "timestamp": timestamp,
                "quaternion": {
                    "x": parse_q(qx),
                    "y": parse_q(qy),
                    "z": parse_q(qz),
                    "w": parse_q(qw)
                },
                "velocity": {
                    "x": parse_v(vx),
                    "y": parse_v(vy),
                    "z": parse_v(vz)
                }
            })

        elif event_type == 0x02: # MOVE
            if self.last_serial != -1:
                serial = msg.get_bit_word(4, 8)
                diff = min((serial - self.last_serial) & 0xFF, 7)
                self.last_serial = serial

                if diff > 0:
                    for i in range(diff - 1, -1, -1):
                        face = msg.get_bit_word(12 + 5 * i, 4)
                        direction = msg.get_bit_word(16 + 5 * i, 1)
                        move_str = "URFDLB"[face] + " '"[direction]
                        move_str = move_str.strip()
                        
                        elapsed = msg.get_bit_word(47 + 16 * i, 16)
                        if elapsed == 0:
                            elapsed = timestamp - self.last_move_timestamp
                        
                        self.cube_timestamp += elapsed
                        
                        cube_events.append({
                            "type": "MOVE",
                            "face": face,
                            "direction": direction,
                            "move": move_str,
                            "serial": (serial - i) & 0xFF,
                            "timestamp": timestamp,
                            "localTimestamp": timestamp if i == 0 else None,
                            "cubeTimestamp": self.cube_timestamp
                        })
                    self.last_move_timestamp = timestamp

        elif event_type == 0x04: # FACELETS
            serial = msg.get_bit_word(4, 8)
            self.last_serial = serial
            
            cp = [msg.get_bit_word(12 + i * 3, 3) for i in range(7)]
            co = [msg.get_bit_word(33 + i * 2, 2) for i in range(7)]
            ep = [msg.get_bit_word(47 + i * 4, 4) for i in range(11)]
            eo = [msg.get_bit_word(91 + i, 1) for i in range(11)]

            cp.append(28 - sum(cp))
            co.append((3 - (sum(co) % 3)) % 3)
            ep.append(66 - sum(ep))
            eo.append((2 - (sum(eo) % 2)) % 2)

            cube_events.append({
                "type": "FACELETS",
                "serial": serial,
                "timestamp": timestamp,
                "state": {"CP": cp, "CO": co, "EP": ep, "EO": eo},
                "facelets": to_kociemba_facelets(cp, co, ep, eo)
            })

        elif event_type == 0x05: # HARDWARE
            hw_major = msg.get_bit_word(8, 8)
            hw_minor = msg.get_bit_word(16, 8)
            sw_major = msg.get_bit_word(24, 8)
            sw_minor = msg.get_bit_word(32, 8)
            gyro_supported = msg.get_bit_word(104, 1)

            hardware_name = ""
            for i in range(8):
                hardware_name += chr(msg.get_bit_word(i * 8 + 40, 8))
            hardware_name = hardware_name.strip('\x00')

            cube_events.append({
                "type": "HARDWARE",
                "timestamp": timestamp,
                "hardwareName": hardware_name,
                "softwareVersion": f"{sw_major}.{sw_minor}",
                "hardwareVersion": f"{hw_major}.{hw_minor}",
                "gyroSupported": gyro_supported == 1
            })

        elif event_type == 0x09: # BATTERY
            battery_level = msg.get_bit_word(8, 8)
            cube_events.append({
                "type": "BATTERY",
                "timestamp": timestamp,
                "batteryLevel": min(battery_level, 100)
            })

        return cube_events
