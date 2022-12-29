import backoff
from eth_typing import HexStr
from sw_utils import IpfsFetchClient
from web3 import Web3

BLS_PUBLIC_KEY_LENGTH = 48
BLS_SIGNATURE_LENGTH = 96


@backoff.on_exception(backoff.expo, Exception, max_time=15)
async def fetch_vault_deposit_data(ipfs_endpoints: list[str], ipfs_hash: str) -> list[HexStr]:
    """Fetches deposit data from the IPFS."""
    ipfs_data = await IpfsFetchClient(ipfs_endpoints).fetch_bytes(ipfs_hash)
    deposit_data_length = BLS_PUBLIC_KEY_LENGTH + BLS_SIGNATURE_LENGTH

    public_keys = []
    for i in range(0, len(ipfs_data), deposit_data_length):
        public_key = ipfs_data[i : i + BLS_PUBLIC_KEY_LENGTH]
        public_keys.append(Web3.to_hex(public_key))

    return public_keys
