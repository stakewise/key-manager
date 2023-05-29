from dataclasses import dataclass
from typing import NewType

from eth_typing import HexStr

BLSPrivkey = NewType('BLSPrivkey', bytes)
ExitSignature = NewType('ExitSignature', HexStr)


@dataclass
class DatabaseKeyRecord:
    public_key: HexStr
    private_key: str
    nonce: str


@dataclass
class ValidatorKeystore:
    private_key: str
    public_key: str
    index: int
    password: str
