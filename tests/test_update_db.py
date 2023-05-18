import unittest
from unittest.mock import patch

from click.testing import CliRunner
from staking_deposit.key_handling.key_derivation.mnemonic import get_mnemonic

from key_manager.commands.create_keys import export_keystores
from key_manager.commands.update_db import update_db
from key_manager.credentials import CredentialManager
from key_manager.language import WORD_LISTS_PATH
from key_manager.settings import GOERLI

from .factories import faker

mnemonic = get_mnemonic(language='english', words_path=WORD_LISTS_PATH)


class TestUpdateDB(unittest.TestCase):
    def test_basic(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            keys_count = 10
            vault = faker.eth_address()
            keystores_dir = './test_data/keystores/'
            keystores_password_file = './test_data/password.txt'
            credentials = CredentialManager.generate_credentials(
                network=GOERLI,
                vault=vault,
                mnemonic=mnemonic,
                count=keys_count,
                start_index=0,
            )

            export_keystores(
                credentials=credentials,
                keystores_dir=keystores_dir,
                password_file=keystores_password_file,
            )

            db_url = 'postgresql://username:pass@hostname/dbname'
            args = [
                '--keystores-dir',
                keystores_dir,
                '--keystores-password-file',
                keystores_password_file,
                '--db-url',
                db_url,
                '--no-confirm',
                '--vault',
                vault
            ]
            with patch('key_manager.commands.update_db.check_db_connection'), patch(
                'key_manager.commands.update_db.Database.fetch_public_keys_count',
                return_value=keys_count,
            ), patch(
                'key_manager.commands.update_db.Database.upload_keys',
                return_value=None,
            ) as db_upload_mock:
                result = runner.invoke(update_db, args)
                assert (
                    f'The database contains {keys_count} validator keys.' in result.output.strip()
                )
                db_upload_mock.assert_called_once()
                results = db_upload_mock.call_args.kwargs['keys']
                assert sorted([x.public_key for x in results]) == sorted(
                    [c.public_key for c in credentials]
                )

                result = runner.invoke(update_db, args)

                assert (
                    f'The database contains {keys_count} validator keys.' in result.output.strip()
                )
