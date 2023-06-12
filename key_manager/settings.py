from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ens.constants import EMPTY_ADDR_HEX
from eth_typing import ChecksumAddress, HexStr
from sw_utils.typings import Bytes32
from web3 import Web3
from web3.types import Wei

MAINNET = 'mainnet'
GOERLI = 'goerli'
GNOSIS = 'gnosis'


class VAULT_TYPE(Enum):
    PRIVATE = 'private'
    PUBLIC = 'public'


@dataclass
class NetworkConfig:
    VAULT_FACTORY_CONTRACT_ADDRESS: ChecksumAddress
    GENESIS_FORK_VERSION: bytes
    DEPOSIT_AMOUNT: Wei
    IS_POA: bool
    GENESIS_VALIDATORS_ROOT: Bytes32

    @property
    def DEPOSIT_AMOUNT_GWEI(self) -> int:
        return int(Web3.from_wei(self.DEPOSIT_AMOUNT, 'gwei'))


NETWORKS = {
    MAINNET: NetworkConfig(
        VAULT_FACTORY_CONTRACT_ADDRESS=Web3.to_checksum_address(EMPTY_ADDR_HEX),
        GENESIS_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x00000000')),
        GENESIS_VALIDATORS_ROOT=Bytes32(
            Web3.to_bytes(
                hexstr=HexStr('0x4b363db94e286120d76eb905340fdd4e54bfe9f06bf33ff6cf5ad27f511bfe95')
            )
        ),
        DEPOSIT_AMOUNT=Web3.to_wei(32, 'ether'),
        IS_POA=True,
    ),
    GOERLI: NetworkConfig(
        VAULT_FACTORY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xFfd31AdCe24fBF18d5BBfe679e2E3e9A321C137F'
        ),
        GENESIS_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x00001020')),
        GENESIS_VALIDATORS_ROOT=Bytes32(
            Web3.to_bytes(
                hexstr=HexStr('0x043db0d9a83813551ee2f33450d23797757d430911a9320530ad8a0eabc43efb')
            )
        ),
        DEPOSIT_AMOUNT=Web3.to_wei(32, 'ether'),
        IS_POA=False,
    ),
    GNOSIS: NetworkConfig(
        VAULT_FACTORY_CONTRACT_ADDRESS=Web3.to_checksum_address(EMPTY_ADDR_HEX),
        GENESIS_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x00000064')),
        GENESIS_VALIDATORS_ROOT=Bytes32(
            Web3.to_bytes(
                hexstr=HexStr('0xf5dcb5564e829aab27264b9becd5dfaa017085611224cb3036f573368dbb9d47')
            )
        ),
        DEPOSIT_AMOUNT=Web3.to_wei(32, 'ether'),
        IS_POA=True,
    ),
}

# Alias
AVAILABLE_NETWORKS = [GOERLI]

DEFAULT_RETRY_TIME = 30

CONFIG_DIR = Path.home() / '.stakewise'
