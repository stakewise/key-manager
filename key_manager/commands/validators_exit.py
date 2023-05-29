import json
from pathlib import Path

import click
import milagro_bls_binding as bls
import requests
from eth_typing import HexAddress, HexStr
from requests.exceptions import HTTPError
from staking_deposit.key_handling.keystore import ScryptKeystore
from sw_utils.signing import get_exit_message_signing_root, is_valid_exit_signature
from sw_utils.typings import ConsensusFork
from web3 import Web3
from web3.beacon import Beacon

from key_manager.config import Config
from key_manager.settings import CONFIG_DIR, NETWORKS
from key_manager.typings import BLSPrivkey, ExitSignature, ValidatorKeystore
from key_manager.validators import validate_eth_address

w3 = Web3()

@click.option(
    '--vault',
    prompt='Enter your vault address',
    help='Vault address',
    type=str,
    callback=validate_eth_address,
)
@click.option(
    '--consensus-endpoint',
    help='Beacon node RPC provider endpoint (default: "http://127.0.0.1:4000").',
    prompt='Enter the beacon node RPC provider endpoint',
    type=str,
    default='http://127.0.0.1:4000',
)
@click.command(help='Performs a voluntary exit.')
def validators_exit(vault: HexAddress, consensus_endpoint: str) -> None:
    config = Config(vault)
    config.load()

    consensus_client = _get_consensus_client(consensus_endpoint)
    fork = _get_consensus_fork(consensus_client)

    keystores_and_passwords = get_keystores_and_passwords(vault, consensus_endpoint)
    if not keystores_and_passwords:
        raise click.ClickException('Keystores not found.')

    for keystore in keystores_and_passwords:
        exit_signature = get_exit_signature(keystore.index, keystore.private_key, fork, config.network)
        epoch = _get_finality_epoch(consensus_client)
        submit_voluntary_exit(epoch, keystore.index, exit_signature, consensus_endpoint)


def _get_consensus_client(consensus_endpoint: str) -> Beacon:
    try:
        consensus_client = Beacon(consensus_endpoint)
        is_syncing = consensus_client.get_syncing().get('data').get('is_syncing')
        if is_syncing:
            raise click.ClickException('could not perform exit: beacon node is syncing.')
    except HTTPError as e:
        raise click.ClickException(f'Beacon node is unavailable: {e}')
    
    return consensus_client


def get_keystores_and_passwords(
    vault: HexAddress,
    consensus_endpoint: str
) -> list[ValidatorKeystore]:
    vault_dir = Path(CONFIG_DIR) / str(vault)
    keystore_paths = list(vault_dir.glob('keystores/*.json'))
    password_file = vault_dir / 'keystores/password.txt'

    with open(password_file, 'r') as f:
        password = f.read().strip()

    keystores = []
    for path in keystore_paths:
        try:
            with open(path, 'r') as f:
                keystore = json.load(f)
            private_key = ScryptKeystore.from_file(path).decrypt(password)
            public_key = keystore['pubkey']
            validator_index = _get_validator_index(public_key, consensus_endpoint)
            keystore = ValidatorKeystore(private_key, public_key, validator_index, password)
            keystores.append(keystore)
        except Exception as e:
            raise click.ClickException(f'Failed to process keystore at {path}: {str(e)}')

    return keystores

def get_exit_signature(
    validator_index: int,
    private_key: HexStr,
    fork: ConsensusFork,
    network: str,
) -> ExitSignature:
    """Generates exit signature"""
    message = get_exit_message_signing_root(
        validator_index=validator_index,
        genesis_validators_root=NETWORKS[network].GENESIS_VALIDATORS_ROOT,
        fork=fork
    )
    exit_signature = bls.Sign(private_key, message)

    return w3.to_hex(exit_signature)


def _get_consensus_fork(consensus_client: Beacon) -> ConsensusFork:
    """Fetches current fork data."""
    fork_data = (consensus_client.get_fork_data())['data']
    return ConsensusFork(
        version=w3.to_bytes(hexstr=fork_data['current_version']), epoch=int(fork_data['epoch'])
    )

def submit_voluntary_exit(
    epoch: int,
    validator_index: int,
    signature: HexStr,
    consensus_endpoint: str
) -> None:
    endpoint = f'{consensus_endpoint}/eth/v1/beacon/pool/voluntary_exits'
    data = {
        'message': {
            'epoch': str(epoch),
            'validator_index': str(validator_index)
        },
        'signature': signature
    }
    print(json.dumps(data))
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(endpoint, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print(json.dumps(response.json()))
    except HTTPError as e:
        raise click.ClickException(f'Failed to submit voluntary exit: {str(e)}')

def _get_validator_index(public_key: HexStr, consensus_endpoint: str) -> int:
    beacon_chain_url = f'{consensus_endpoint}/eth/v1/beacon/states/head/validators/0x{public_key}'
    response = requests.get(beacon_chain_url)
    response.raise_for_status()

    data = response.json()
    return int(data['data']['index'])

def _get_finality_epoch(consensus_client: Beacon) -> int:
    checkpoints = consensus_client.get_finality_checkpoint()
    return int(checkpoints['data']['finalized']['epoch'])
