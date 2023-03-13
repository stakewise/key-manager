import os
import unittest
from unittest.mock import patch

from click.testing import CliRunner
from eth_typing import BLSPrivateKey
from py_ecc.bls import G2ProofOfPossession
from staking_deposit.key_handling.key_derivation.mnemonic import get_mnemonic, get_seed
from staking_deposit.key_handling.key_derivation.path import path_to_nodes
from staking_deposit.key_handling.key_derivation.tree import (
    derive_child_SK,
    derive_master_SK,
)
from web3 import Web3

from key_manager.commands.sync_web3signer import sync_web3signer
from key_manager.contrib import bytes_to_str
from key_manager.credentials import COIN_TYPE, PURPOSE
from key_manager.encoder import Encoder
from key_manager.language import WORD_LISTS_PATH
from key_manager.typings import DatabaseKeyRecord

w3 = Web3()


class TestSyncWeb3signer(unittest.TestCase):
    def test_basic(self):
        db_url = 'postgresql://username:pass@hostname/dbname'
        keys_count = 3
        encoder = Encoder()

        mnemonic = get_mnemonic(language='english', words_path=WORD_LISTS_PATH)
        private_keys, db_records = _generate_keys(
            mnemonic=mnemonic, encoder=encoder, keys_count=keys_count
        )

        runner = CliRunner()
        args = [
            '--db-url',
            db_url,
            '--decryption-key-env',
            'DECRYPT_ENV',
            '--output-dir',
            './web3signer',
        ]

        with runner.isolated_filesystem(), patch(
            'key_manager.commands.sync_web3signer.check_db_connection'
        ), patch(
            'key_manager.commands.sync_web3signer.Database.fetch_keys',
            return_value=db_records,
        ), patch.dict(
            os.environ, {'DECRYPT_ENV': encoder.cipher_key_str}
        ):
            result = runner.invoke(sync_web3signer, args)
            assert result.exit_code == 0
            output = f'Web3Signer now uses {len(db_records)} private keys.\n'
            assert output.strip() == result.output.strip()

            for index, private_key in enumerate(private_keys):
                key_hex = Web3.to_hex(int(private_key))
                with open(f'./web3signer/key_{index}.yaml', encoding='utf-8') as f:
                    s = f"""keyType: BLS
privateKey: \'0x{key_hex[2:].zfill(64)}\'
type: file-raw"""
                    s += '\n'
                    assert f.read() == s

            # second run
            result = runner.invoke(sync_web3signer, args)

            assert result.exit_code == 0
            output = 'Keys already synced to the last version.\n'
            assert output.strip() == result.output.strip()


def _generate_keys(
    mnemonic, encoder, keys_count
) -> tuple[list[BLSPrivateKey], list[DatabaseKeyRecord]]:
    private_keys, db_records = [], []

    for index in range(keys_count):
        seed = get_seed(mnemonic=mnemonic, password='')  # nosec
        private_key = BLSPrivateKey(derive_master_SK(seed))
        signing_key_path = f'm/{PURPOSE}/{COIN_TYPE}/{index}/0/0'
        nodes = path_to_nodes(signing_key_path)

        for node in nodes:
            private_key = BLSPrivateKey(derive_child_SK(parent_SK=private_key, index=node))

        encrypted_private_key, nonce = encoder.encrypt(str(private_key))

        private_keys.append(private_key)
        db_records.append(
            DatabaseKeyRecord(
                public_key=w3.to_hex(G2ProofOfPossession.SkToPk(private_key)),
                private_key=bytes_to_str(encrypted_private_key),
                nonce=bytes_to_str(nonce),
            )
        )
    return private_keys, db_records