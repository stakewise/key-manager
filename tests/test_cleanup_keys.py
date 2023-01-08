import random
import unittest
from unittest.mock import patch

from click.testing import CliRunner
from sw_utils.consensus import ValidatorStatus

from key_manager.commands.cleanup_keys import cleanup_keys
from key_manager.settings import MAINNET

from .factories import faker


class TestCleanupKeys(unittest.TestCase):
    def test_basic(self):
        vault = faker.eth_address()
        w3signer_public_keys = [faker.eth_public_key() for x in range(5)]
        deposit_data_public_keys = w3signer_public_keys[:4]
        consensus_data = [
            {'status': ValidatorStatus.ACTIVE_ONGOING, 'validator': {'pubkey': pubkey}}
            for pubkey in w3signer_public_keys[:3]
        ] + [
            {
                'status': ValidatorStatus.EXITED_SLASHED,
                'validator': {'pubkey': w3signer_public_keys[3]},
            }
        ]
        runner = CliRunner()
        args = [
            '--network',
            MAINNET,
            '--vault',
            vault,
            '--execution-endpoint',
            'https://example.com',
            '--consensus-endpoint',
            'https://example.com',
            '--web3signer-endpoint',
            'https://example.com',
        ]
        with patch(
            'key_manager.commands.cleanup_keys.Web3signer.list_keys',
            return_value=w3signer_public_keys,
        ), patch(
            'key_manager.commands.cleanup_keys.Web3signer.delete_keys',
        ) as delete_keys_mock, patch(
            'key_manager.commands.cleanup_keys.get_current_number',
            return_value=random.randint(10000, 1000000),
        ), patch(
            'key_manager.commands.cleanup_keys.VaultContract.'
            'get_last_validators_root_updated_event',
            return_value='someipfshash',
        ), patch(
            'key_manager.commands.cleanup_keys.fetch_vault_deposit_data',
            return_value=deposit_data_public_keys,
        ), patch(
            'key_manager.commands.cleanup_keys.get_validators',
            return_value=consensus_data,
        ):
            result = runner.invoke(cleanup_keys, args)

            assert result.exit_code == 0

            output = (
                'Checking validator keys:\t\t\n'
                'Found 2 unused keys, remove them from the Web3Signer? [Y/n]: \n'
                'Done. Deleted 2 unused keys from https://example.com.\n'
            )

            assert output.strip() == result.output.strip()
            delete_keys_mock.assert_called_once_with(w3signer_public_keys[3:])
