import glob
import json
import os

import click
from py_ecc.bls import G2ProofOfPossession
from staking_deposit.key_handling.keystore import ScryptKeystore
from web3 import Web3

from key_manager.contrib import bytes_to_str
from key_manager.database import Database, check_db_connection
from key_manager.encoder import Encoder
from key_manager.typings import DatabaseKeyRecord
from key_manager.validators import validate_db_uri

w3 = Web3()


@click.option(
    '--keystores-dir',
    required=False,
    help='The directory with validator keys in the EIP-2335 standard.'
    ' Defaults to ./data/keystores.',
    default='./data/keystores',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    '--keystores-password-file',
    required=False,
    help='The path to file with password for encrypting the keystores.'
    ' Defaults to ./data/keystores/password.txt.',
    default='./data/keystores/password.txt',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    '--db-url',
    help='The database connection address.',
    prompt="Enter the database connection string, ex. 'postgresql://username:pass@hostname/dbname'",
    callback=validate_db_uri,
)
@click.option(
    '--encryption-key',
    help='The key for encrypting database record. '
         'If you are upload new keystores use the same encryption key.',
    required=False,
    prompt=False,

)
@click.option(
    '--no-confirm',
    is_flag=True,
    default=False,
    help='Skips confirmation messages when provided.',
)
@click.command(help='Encrypt and load validator keys from the keystores into the database.')
def update_db(
    keystores_dir: str,
    keystores_password_file: str,
    db_url: str,
    encryption_key: str | None,
    no_confirm: bool,
) -> None:
    check_db_connection(db_url)

    with open(keystores_password_file, 'r', encoding='utf-8') as f:
        keystores_password = f.read().strip()

    private_keys = []

    with click.progressbar(
            glob.glob(os.path.join(keystores_dir, '*.json')),
            label='Loading keystores...\t\t',
            show_percent=False,
            show_pos=True,
    ) as _keystore_files:
        for filename in _keystore_files:
            try:
                keystore = ScryptKeystore.from_file(filename).decrypt(keystores_password)
                private_keys.append(int.from_bytes(keystore, 'big'))
            except (json.JSONDecodeError, KeyError) as e:
                click.secho(
                    f'Failed to load keystore {filename}. Error: {str(e)}.',
                    fg='red',
                )

    database = Database(
        db_url=db_url,
    )
    encoder = Encoder(encryption_key)

    database_records = _encrypt_private_keys(
        private_keys=private_keys,
        encoder=encoder,
    )
    if not no_confirm:
        click.confirm(
            f'Generated {len(private_keys)} validator keys, upload them to the database?',
            default=True,
            abort=True,
        )
    database.upload_keys(keys=database_records)
    total_keys_count = database.fetch_public_keys_count()

    click.clear()

    click.secho(
        f'The database contains {total_keys_count} validator keys.\n'
        f"Save decryption key: '{encoder.cipher_key_str}'",
        bold=True,
        fg='green',
    )


def _encrypt_private_keys(
    private_keys: list[int], encoder: Encoder

) -> list[DatabaseKeyRecord]:
    """
    Returns prepared database key records from the private keys.
    """

    click.secho('Encrypting database keys...', bold=True)
    key_records: list[DatabaseKeyRecord] = []
    for private_key in private_keys:
        encrypted_private_key, nonce = encoder.encrypt(str(private_key))

        key_record = DatabaseKeyRecord(
            public_key=w3.to_hex(G2ProofOfPossession.SkToPk(private_key)),
            private_key=bytes_to_str(encrypted_private_key),
            nonce=bytes_to_str(nonce),
        )

        if key_record not in key_records:
            key_records.append(key_record)

    return key_records
