import json
import os

import backoff
import click
from eth_typing import BlockNumber, ChecksumAddress, HexAddress, HexStr
from eth_utils import is_address, to_checksum_address
from web3 import Web3
from web3.contract import AsyncContract

from key_manager.settings import NETWORKS


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


class ValidatorRegistryContract(BaseContract):
    abi_path = 'abis/IValidatorsRegistry.json'

    @backoff.on_exception(backoff.expo, Exception, max_time=15)
    async def get_latest_network_validator_public_keys(
        self, from_block: BlockNumber, to_block: BlockNumber
    ) -> set[HexStr]:
        events = await self.contract.events.DepositEvent.getLogs(
            fromBlock=from_block, toBlock=to_block
        )
        return {Web3.to_hex(event['args']['pubkey']) for event in events}


class VaultFactoryContract(BaseContract):
    abi_path = 'abis/IEthVaultFactory.json'

    @backoff.on_exception(backoff.expo, Exception, max_time=15)
    async def compute_addresses(self, admin_address: ChecksumAddress):
        return await self.contract.functions.computeAddresses(admin_address).call()


class VaultContract(BaseContract):
    abi_path = 'abis/IBaseVault.json'

    @backoff.on_exception(backoff.expo, Exception, max_time=15)
    async def get_last_validators_root_ipfs_hash(self, current_block: BlockNumber) -> str | None:
        """Fetches the last rewards update."""
        chunk_size = 1000
        from_block, to_block = current_block - chunk_size, current_block
        while from_block > self.genesis_block:
            events = await self.contract.events.ValidatorsRootUpdated.getLogs(
                fromBlock=from_block,
                toBlock=to_block,
            )
            if events:
                return events[-1]['args']['validatorsIpfsHash']
            from_block, to_block = BlockNumber(to_block - chunk_size), BlockNumber(
                to_block - chunk_size
            )

        return None


@backoff.on_exception(backoff.expo, Exception, max_time=15)
async def get_current_number(execution_client) -> BlockNumber:
    """Fetches the fork safe block number."""
    return await execution_client.eth.get_block_number()  # type: ignore


async def generate_vault_address(
    admin: HexAddress, vault_type: str, execution_client: Web3, network: str
):
    if vault_type and admin:
        try:
            factory_address = NETWORKS[network].get_vault_factory_contract_addresses(vault_type)
            return (
                await VaultFactoryContract(
                    address=factory_address,
                    execution_client=execution_client,
                ).compute_addresses(admin_address=Web3.to_checksum_address(admin))
            )[0]
        except BaseException as e:
            raise click.ClickException('Failed to generate the vault address') from e
    elif vault_type or admin:
        raise click.BadParameter('Provide only the vault address or combination '
                                 'of the admin address and the vault type')
    else:
        vault = click.prompt('Enter the vault address for which the validator keys are generated')
        if is_address(vault):
            return to_checksum_address(vault)
        raise click.BadParameter('Invalid Ethereum address')
