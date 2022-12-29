import json
import os

import backoff
from eth_typing import BlockNumber, ChecksumAddress, HexStr
from web3 import Web3
from web3.contract import AsyncContract


class BaseContract:
    abi_path: str
    address: ChecksumAddress
    genesis_block: BlockNumber

    def __init__(self, genesis_block, address, execution_client):
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


class VaultContract(BaseContract):
    abi_path = 'abis/IBaseVault.json'

    @backoff.on_exception(backoff.expo, Exception, max_time=15)
    async def get_last_validators_root_updated_event(
        self, current_block: BlockNumber
    ) -> str | None:
        """Fetches the last rewards update."""
        chunk_size = 1000
        from_block, to_block = current_block - chunk_size, current_block
        while from_block > self.genesis_block:
            events = await self.contract.events.ValidatorsRootUpdated.getLogs(
                fromBlock=from_block,
                toBlock=to_block,
            )
            if events:
                return events[:-1]['args']['validatorsIpfsHash']
            from_block, to_block = BlockNumber(to_block - chunk_size), BlockNumber(
                to_block - chunk_size
            )

        return None


@backoff.on_exception(backoff.expo, Exception, max_time=15)
async def get_current_number(execution_client) -> BlockNumber:
    """Fetches the fork safe block number."""
    return await execution_client.eth.get_block_number()  # type: ignore
