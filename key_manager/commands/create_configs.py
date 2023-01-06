import json
from pathlib import Path

import click
import yaml
from eth_typing import HexStr

from key_manager.validators import validate_eth_address
from key_manager.web3signer import Web3signer

VALIDATOR_DEFINITIONS_FILENAME = 'validator_definitions.yml'
SIGNER_KEYS_FILENAME = 'signer_keys.yml'
PROPOSER_CONFIG_FILENAME = 'proposer_config.json'


# pylint: disable-next=unused-argument
def validate_validator_index(ctx, param, value):
    total_validators = ctx.params.get('total_validators', 0)
    if not total_validators or total_validators <= value:
        raise click.BadParameter('validator-index must be less than total-validators')
    return value


@click.option(
    '--fee-recipient',
    help='The recipient address for MEV & priority fees.',
    prompt='Enter the recipient address for MEV & priority fees',
    type=str,
    callback=validate_eth_address,
)
@click.option(
    '--validator-index',
    help='The validator index to generate the configuration files.',
    prompt='Enter the validator index to generate the configuration files',
    type=int,
    callback=validate_validator_index,
)
@click.option(
    '--total-validators',
    help='The total number of validators connected to the web3signer.',
    prompt='Enter the total number of validators connected to the web3signer',
    type=click.IntRange(min=1),
)
@click.option(
    '--web3signer-endpoint',
    help='The endpoint of the web3signer service.',
    prompt='Enter the endpoint of the web3signer service',
    type=str,
)
@click.option(
    '--output-dir',
    required=False,
    help='The directory to save configuration files. Defaults to ./data/configs.',
    default='./data/configs',
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
)
@click.option(
    '--disable-proposal-builder',
    is_flag=True,
    default=False,
    help='Disable proposal builder for Teku and Prysm clients',
)
@click.command(
    help='Creates validator configuration files for Lighthouse, '
    'Prysm, and Teku clients to sign data using web3signer.'
)
def create_configs(
    fee_recipient: str,
    total_validators: int,
    validator_index: int,
    web3signer_endpoint: str,
    output_dir: str,
    disable_proposal_builder: bool,
) -> None:
    web3signer = Web3signer(web3signer_endpoint)
    web3signer_keys = web3signer.list_keys()

    if not web3signer_keys:
        raise click.ClickException('Web3signer does not contain any keys')

    keys_per_validator = len(web3signer_keys) // total_validators

    start_index = keys_per_validator * validator_index
    if validator_index == total_validators - 1:
        validator_keys = web3signer_keys[start_index:]
    else:
        validator_keys = web3signer_keys[start_index: start_index + keys_per_validator]

    Path.mkdir(Path(output_dir), exist_ok=True, parents=True)

    # lighthouse
    validator_definitions_filepath = str(Path(output_dir, VALIDATOR_DEFINITIONS_FILENAME))
    _generate_lighthouse_config(
        public_keys=validator_keys,
        web3signer_url=web3signer_endpoint,
        fee_recipient=fee_recipient,
        filepath=validator_definitions_filepath,
    )

    # teku/prysm
    signer_keys_filepath = str(Path(output_dir, SIGNER_KEYS_FILENAME))
    _generate_signer_keys_config(
        public_keys=validator_keys, filepath=signer_keys_filepath
    )

    proposer_config_filepath = str(Path(output_dir, PROPOSER_CONFIG_FILENAME))
    _generate_proposer_config(
        fee_recipient=fee_recipient,
        proposal_builder_enabled=not disable_proposal_builder,
        filepath=proposer_config_filepath,
    )

    click.clear()
    click.secho(
        f'Done. '
        f'Generated configs with {len(validator_keys)} keys for validator #{validator_index}.\n'
        f'Validator definitions for Lighthouse saved to {validator_definitions_filepath} file.\n'
        f'Signer keys for Teku\\Prysm saved to {signer_keys_filepath} file.\n'
        f'Proposer config for Teku\\Prysm saved to {proposer_config_filepath} file.\n',
        bold=True,
        fg='green',
    )


def _generate_lighthouse_config(
    public_keys: list[HexStr],
    web3signer_url: str,
    fee_recipient: str,
    filepath: str,
) -> None:
    """
    Generate config for Lighthouse clients
    """
    items = [
        {
            'enabled': True,
            'voting_public_key': public_key,
            'type': 'web3signer',
            'url': web3signer_url,
            'suggested_fee_recipient': fee_recipient,
        }
        for public_key in public_keys
    ]

    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(items, f, explicit_start=True)


def _generate_signer_keys_config(public_keys: list[HexStr], filepath: str) -> None:
    """
    Generate config for Teku and Prysm clients
    """
    keys = ','.join([f'"{public_key}"' for public_key in public_keys])
    config = f"""validators-external-signer-public-keys: [{keys}]"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(config)


def _generate_proposer_config(
    fee_recipient: str,
    proposal_builder_enabled: bool,
    filepath: str,
) -> None:
    """
    Generate proposal config for Teku and Prysm clients
    """
    config = {
        'default_config': {
            'fee_recipient': fee_recipient,
            'builder': {
                'enabled': proposal_builder_enabled,
            },
        },
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
