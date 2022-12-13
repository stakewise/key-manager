import unittest
from unittest.mock import patch

from click.testing import CliRunner

from key_manager.commands.create_mnemonic import create_mnemonic

from .factories import faker

mnemonic = ' '.join([faker.word() for x in range(24)])


@patch('key_manager.language.get_mnemonic', return_value=mnemonic)
class TestCreateMnemonic(unittest.TestCase):

    def test_basic(self, mnemonic_mock):
        runner = CliRunner()
        args = ['--language', 'english']
        result = runner.invoke(create_mnemonic, args, input=f'a\n{mnemonic}\n')
        assert result.exit_code == 0
        mnemonic_mock.assert_called_once()
        assert mnemonic in result.output.strip()
        assert 'done' in result.output.strip()

    def test_bad_verify(self, mnemonic_mock):
        runner = CliRunner()
        args = ['--language', 'english']
        result = runner.invoke(create_mnemonic, args, input=f'a\n{mnemonic} bad\na\n{mnemonic}\n')
        print(result.output)
        assert result.exit_code == 0
        mnemonic_mock.assert_called_once()
        assert mnemonic in result.output.strip()
        assert 'done' in result.output.strip()

    def test_no_verify(self, mnemonic_mock):
        runner = CliRunner()
        args = ['--language', 'english', '--no-verify']
        result = runner.invoke(create_mnemonic, args)
        assert result.exit_code == 0
        mnemonic_mock.assert_called_once()
        output = f"""
        This is your seed phrase. Write it down and store it safely, it is the ONLY way to recover your validator keys.\n\n
{mnemonic}\n\n
done.
"""
        assert result.output.strip() == output.strip()

    def test_bad_language(self, *args):
        runner = CliRunner()
        args = ['--language', 'bad', '--no-verify']
        result = runner.invoke(create_mnemonic, args)
        assert result.exit_code == 2
        assert "Invalid value for '--language': 'bad' is not one of" in result.output.strip()
