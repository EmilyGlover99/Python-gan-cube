from Crypto.Cipher import AES

class GanGen2CubeEncrypter:
    def __init__(self, key: list, iv: list, salt: list):
        if len(key) != 16:
            raise ValueError("Key must be 16 bytes long")
        if len(iv) != 16:
            raise ValueError("Iv must be 16 bytes long")
        if len(salt) != 6:
            raise ValueError("Salt must be 6 bytes long")

        self._key = bytearray(key)
        self._iv = bytearray(iv)
        for i in range(6):
            self._key[i] = (key[i] + salt[i]) % 0xFF
            self._iv[i] = (iv[i] + salt[i]) % 0xFF

    def _encrypt_chunk(self, data: bytearray, offset: int):
        cipher = AES.new(self._key, AES.MODE_CBC, self._iv)
        chunk = cipher.encrypt(bytes(data[offset:offset+16]))
        data[offset:offset+16] = chunk

    def _decrypt_chunk(self, data: bytearray, offset: int):
        cipher = AES.new(self._key, AES.MODE_CBC, self._iv)
        chunk = cipher.decrypt(bytes(data[offset:offset+16]))
        data[offset:offset+16] = chunk

    def encrypt(self, data: bytes) -> bytes:
        if len(data) < 16:
            raise ValueError("Data must be at least 16 bytes long")
        res = bytearray(data)
        self._encrypt_chunk(res, 0)
        if len(res) > 16:
            self._encrypt_chunk(res, len(res) - 16)
        return bytes(res)

    def decrypt(self, data: bytes) -> bytes:
        if len(data) < 16:
            raise ValueError("Data must be at least 16 bytes long")
        res = bytearray(data)
        if len(res) > 16:
            self._decrypt_chunk(res, len(res) - 16)
        self._decrypt_chunk(res, 0)
        return bytes(res)

class GanGen3CubeEncrypter(GanGen2CubeEncrypter):
    pass

class GanGen4CubeEncrypter(GanGen2CubeEncrypter):
    pass
