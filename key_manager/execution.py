import json
import os

import backoff
import click
from eth_typing import BlockNumber, ChecksumAddress, HexAddress
from eth_utils import to_checksum_address
from web3 import Web3
from web3.contract import AsyncContract

from key_manager.settings import DEFAULT_RETRY_TIME, NETWORKS, VAULT_TYPE


class BaseContract:
    abi_path: str
    address: ChecksumAddress
    genesis_block: BlockNumber

    def __init__(self, address, execution_client, genesis_block=BlockNumber(0)):
        self.address = address
        self.execution_client = execution_client
        self.genesis_block = genesis_block

    @property
    def contract(self) -> AsyncContract:
        current_dir = os.path.dirname(__file__)
        with open(os.path.join(current_dir, self.abi_path), encoding='utf-8') as f:
            abi = json.load(f)
        return self.execution_client.eth.contract(abi=abi, address=self.address)


class VaultFactoryContract(BaseContract):
    abi_path = 'abis/IEthVaultFactory.json'

    @backoff.on_exception(backoff.expo, Exception, max_time=DEFAULT_RETRY_TIME)
    async def compute_addresses(
        self, admin_address: ChecksumAddress, is_private: bool
    ) -> ChecksumAddress:
        address, _ = await self.contract.functions.computeAddresses(
            admin_address, is_private
        ).call()
        return to_checksum_address(address)


async def generate_vault_address(
    admin: HexAddress, vault_type: str, execution_client: Web3, network: str
) -> ChecksumAddress:
    try:
        is_private = bool(vault_type == VAULT_TYPE.PRIVATE.value)
        return await VaultFactoryContract(
            address=NETWORKS[network].VAULT_FACTORY_CONTRACT_ADDRESS,
            execution_client=execution_client,
        ).compute_addresses(admin_address=Web3.to_checksum_address(admin), is_private=is_private)
    except BaseException as e:
        raise click.ClickException('Failed to generate the vault address') from e
