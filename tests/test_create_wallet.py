import json
import random
import unittest
from unittest.mock import patch

from click.testing import CliRunner
from eth_account import Account
from staking_deposit.key_handling.key_derivation.mnemonic import get_mnemonic

from key_manager.commands.create_wallet import create_wallet
from key_manager.language import WORD_LISTS_PATH


class TestCreateWallet(unittest.TestCase):
    def test_basic(self):
        runner = CliRunner()
        Account.enable_unaudited_hdwallet_features()
        mnemonic = get_mnemonic(language='english', words_path=WORD_LISTS_PATH)
        account = Account().from_mnemonic(mnemonic=mnemonic)
        ts = random.randint(1600000000, 1700000000)
        args = [
            '--mnemonic',
            f'"{mnemonic}"',
        ]
        with runner.isolated_filesystem(), patch(
            'key_manager.credentials.time.time',
            return_value=ts,
        ):
            result = runner.invoke(create_wallet, args)
            assert result.exit_code == 0
            filename = f'{account.address}-{ts}.json'
            output = f'Done. Wallet {filename} saved to ./wallet directory\n'
            assert output.strip() == result.output.strip()
            with open(f'./wallet/{filename}', encoding='utf-8') as f:
                data = json.load(f)
                assert data.get('address') == account.address.lower()[2:]
            with open('./wallet/password.txt', encoding='utf-8') as f:
                assert len(f.readline()) == 20
