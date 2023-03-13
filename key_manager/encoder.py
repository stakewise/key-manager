from functools import cached_property
from typing import cast

# pycryptodome lib used
from Crypto.Cipher import AES  # nosec
from Crypto.Cipher._mode_eax import EaxMode  # nosec
from Crypto.Random import get_random_bytes  # nosec

from key_manager.contrib import bytes_to_str, str_to_bytes

CIPHER_KEY_LENGTH = 32
NONCE = b'stakewise'


class Decoder:
    def __init__(self, decryption_key: str):
        self.decryption_key = decryption_key

    def decrypt(self, data: str, nonce: str) -> str:
        cipher = self._restore_cipher(nonce=nonce)
        private_key = cipher.decrypt(str_to_bytes(data))
        return private_key.decode('ascii')

    def _restore_cipher(self, nonce: str) -> EaxMode:
        cipher = AES.new(str_to_bytes(self.decryption_key), AES.MODE_EAX, nonce=str_to_bytes(nonce))
        return cast(EaxMode, cipher)


class Encoder:
    def __init__(self, cipher_key_str: str = None):
        if cipher_key_str:
            self.cipher_key = str_to_bytes(cipher_key_str)
        else:
            self.cipher_key = self._generate_cipher_key()

    @cached_property
    def cipher_key_str(self) -> str:
        return bytes_to_str(self.cipher_key)

    def encrypt(self, data: str):
        cipher = self._get_cipher()
        encrypted_data = cipher.encrypt(bytes(data, 'ascii'))
        return encrypted_data, cipher.nonce

    def _generate_cipher_key(self) -> bytes:
        return get_random_bytes(CIPHER_KEY_LENGTH)

    def _get_cipher(self) -> EaxMode:
        cipher = AES.new(self.cipher_key, AES.MODE_EAX, nonce=NONCE)
        return cast(EaxMode, cipher)
