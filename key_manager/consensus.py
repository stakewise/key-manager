import backoff
from eth_typing import HexStr
from sw_utils import ExtendedAsyncBeacon

from key_manager.settings import DEFAULT_RETRY_TIME


@backoff.on_exception(backoff.expo, Exception, max_time=DEFAULT_RETRY_TIME)
async def get_validators(consensus_client: ExtendedAsyncBeacon, public_keys: list[HexStr]) -> dict:
    return (await consensus_client.get_validators_by_ids(public_keys))['data']
