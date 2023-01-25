from dataclasses import dataclass
from enum import Enum

from ens.constants import EMPTY_ADDR_HEX
from eth_typing import BlockNumber, ChecksumAddress, HexStr
from web3 import Web3
from web3.types import Wei

IPFS_ENDPOINTS = [
    'https://stakewise.infura-ipfs.io',
    'http://cloudflare-ipfs.com',
    'https://gateway.pinata.cloud',
    'https://ipfs.io',
]

MAINNET = 'mainnet'
GOERLI = 'goerli'
GNOSIS = 'gnosis'


class VAULT_TYPE(Enum):
    PRIVATE = 'private'
    PUBLIC = 'public'


@dataclass
class NetworkConfig:
    VAULT_FACTORY_CONTRACT_ADDRESS: ChecksumAddress
    VAULT_CONTRACT_GENESIS_BLOCK: BlockNumber
    VALIDATORS_REGISTRY_CONTRACT_ADDRESS: ChecksumAddress
    VALIDATORS_REGISTRY_GENESIS_BLOCK: BlockNumber
    MAX_KEYS_PER_VALIDATOR: int
    BEACON_SYNC_BLOCK_DISTANCE: int
    GENESIS_FORK_VERSION: bytes
    DEPOSIT_AMOUNT: Wei
    IS_POA: bool

    @property
    def DEPOSIT_AMOUNT_GWEI(self) -> int:
        return int(Web3.from_wei(self.DEPOSIT_AMOUNT, 'gwei'))


NETWORKS = {
    MAINNET: NetworkConfig(
        VAULT_FACTORY_CONTRACT_ADDRESS=Web3.to_checksum_address(EMPTY_ADDR_HEX),
        VAULT_CONTRACT_GENESIS_BLOCK=BlockNumber(0),
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(EMPTY_ADDR_HEX),
        VALIDATORS_REGISTRY_GENESIS_BLOCK=BlockNumber(0),
        MAX_KEYS_PER_VALIDATOR=100,
        BEACON_SYNC_BLOCK_DISTANCE=2000,
        GENESIS_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x00000000')),
        DEPOSIT_AMOUNT=Web3.to_wei(32, 'ether'),
        IS_POA=True,
    ),
    GOERLI: NetworkConfig(
        VAULT_FACTORY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x3bedaA84b063AC07d4cD207aF70f4634613B5619'
        ),
        VAULT_CONTRACT_GENESIS_BLOCK=BlockNumber(8368607),
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xff50ed3d0ec03aC01D4C79aAd74928BFF48a7b2b'
        ),
        VALIDATORS_REGISTRY_GENESIS_BLOCK=BlockNumber(4367321),
        MAX_KEYS_PER_VALIDATOR=100,
        BEACON_SYNC_BLOCK_DISTANCE=2000,
        GENESIS_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x00001020')),
        DEPOSIT_AMOUNT=Web3.to_wei(32, 'ether'),
        IS_POA=False,
    ),
    GNOSIS: NetworkConfig(
        VAULT_FACTORY_CONTRACT_ADDRESS=Web3.to_checksum_address(EMPTY_ADDR_HEX),
        VAULT_CONTRACT_GENESIS_BLOCK=BlockNumber(0),
        VALIDATORS_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(EMPTY_ADDR_HEX),
        VALIDATORS_REGISTRY_GENESIS_BLOCK=BlockNumber(0),
        MAX_KEYS_PER_VALIDATOR=100,
        BEACON_SYNC_BLOCK_DISTANCE=2000,
        GENESIS_FORK_VERSION=Web3.to_bytes(hexstr=HexStr('0x00000064')),
        DEPOSIT_AMOUNT=Web3.to_wei(1, 'ether'),
        IS_POA=True,
    ),
}

# Alias
AVAILABLE_NETWORKS = [GOERLI]

DEFAULT_RETRY_TIME = 30
