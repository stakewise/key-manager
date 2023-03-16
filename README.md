# Stakewise V3 key manager

Key manager generates validators keys and deposit data for the validators, allow to generate mnemonic and hot wallet. Also it's helps to manage validator's keys in web3signer infrastructure.

See [releases page](https://github.com/stakewise/key-manager/releases) to download and decompress the corresponding binary files.

## Key management commands

### 1. Create mnemonic
Creates the mnemonic used to derive validator keys.
```bash
# ./key-manager create-mnemonic --language english
This is your seed phrase. Write it down and store it safely, it is the ONLY way to recover your validator keys.

pumpkin anxiety private salon inquiry ....


Press any key when you have written down your mnemonic.

Please type your mnemonic (separated by spaces) to confirm you have written it down

: pumpkin anxiety private salon inquiry ....

done.
```
#### Options:
- `--language` - Choose your mnemonic language
- `--no-verify` - Skips mnemonic verification when provided.

**NB! You must store the generated mnemonic in a secure cold storage.
It will allow you to restore the keys in case the Vault will get corrupted or lost.**

### 2. Create keys
Creates deposit data and validator keystores files for operator service:

```bash
# ./key-manager create-keys
Enter the number of the validator keys to generate: 10
Enter the mnemonic for generating the validator keys: pumpkin anxiety private salon inquiry ....
Enter the network name (goerli) [goerli]:
Enter the vault address for which the validator keys are generated: 0x56FED...07E7
Enter the mnemonic start index for generating validator keys [0]:
Creating validator keys:		  [####################################]  10/10
Generating deposit data JSON		  [####################################]  10/10
Exporting validator keystores		  [####################################]  10/10

Done. Generated 10 keys for 0x56FED...07E7 vault.
Keystores saved to ./data/keystores file
Deposit data saved to ./data/deposit_data.json file
Next mnemonic start index saved to ./mnemonic_next_index.txt file
```
#### Options:
- `--network` - The network to generate the deposit data for.
- `--mnemonic` - The mnemonic for generating the validator keys.
- `--count` - The number of the validator keys to generate.
- `--vault` or `--withdrawal-address` -The withdrawal address where the funds will be sent after validators’ withdrawals.
- `--admin` - The vault admin address.
- `--vault-type` - The vault type.
- `--execution_endpoint` - The endpoint of the execution node used for computing the withdrawal address..
- `--deposit-data-file` - The path to store the deposit data file. Defaults to ./data/deposit_data.json.
- `--keystores` -The directory to store the validator keys in the EIP-2335 standard. Defaults to ./data/keystores.
- `--password-file` - The path to store randomly generated password for encrypting the keystores. Defaults to ./data/keystores/password.txt.
- `--mnemonic-start-index` - The index of the first validator's keys you wish to generate. If this is your first time generating keys with this mnemonic, use 0. If you have generated keys using this mnemonic before, add --mnemonic-next-index-file flag or specify the next index from which you want to start generating keys from (eg, if you've generated 4 keys before (keys #0, #1, #2, #3) then enter 4 here.
- `--mnemonic-next-index-file` - The path where to store the mnemonic index to use for generating next validator keys. Used to always generate unique validator keys. Defaults to ./mnemonic_next_index.txt.


### 3. Create wallets

Creates the encrypted hot wallet from the mnemonic.

```bash
# ./key-manager  create-wallet
Enter the mnemonic for generating the wallet: pumpkin anxiety private salon inquiry ...
Done. Wallet 0xf5fF7...B914a-1677838759.json saved to ./wallet directory
```
#### Options:
- `--mnemonic` - The mnemonic for generating the validator keys.
- `--wallet-dir` - The directory to save encrypted wallet and password files. Defaults to ./wallet.

### Web3Signer infrastructure commands

### 1. Update database
Encrypt and load validator keys from keystore files into the database

```bash
# ./key-manager update-db --db-url postgresql://postgres:postgres@localhost:5432/web3signer --keystores-dir ./data/keystores --keystores-password-file ./data/keystores/password.txt
Loading keystores...              [####################################]  10/10
Encrypting database keys...
Generated 10 validator keys, upload them to the database? [Y/n]: Y
The database contains 10 validator keys.
Save decryption key: '<DECRYPTION KEYS>'
```
#### Options:
- `--keystores-dir` - The directory with validator keys in the EIP-2335 standard. Defaults to ./data/keystores.
- `--keystores-password-file` - The path to file with password for encrypting the keystores. Defaults to ./data/keystores/password.txt.
- `--db-url` - The database connection address.
- `--encryption-key` - The key for encrypting database record. If you are upload new keystores use the same encryption key.
- `--no-confirm` - Skips confirmation messages when provided.

**NB! You must store the decryption key in a secure place.
It will allow you to upload new keystores in the existing database**

### 2. Sync validator configs
Creates validator configuration files for Lighthouse, Prysm, and Teku clients to sign data using keys form database.
```bash
# ./key-manager sync-validator
Enter the recipient address for MEV & priority fees: 0xB31...1
Enter the endpoint of the web3signer service: https://web3signer-example.com
Enter the database connection string, ex. 'postgresql://username:pass@hostname/dbname': postgresql://postgres:postgres@localhost/web3signer
Enter the total number of validators connected to the web3signer: 30
Enter the validator index to generate the configuration files: 5


Done. Generated configs with 50 keys for validator #5.
Validator definitions for Lighthouse saved to data/configs/validator_definitions.yml file.
Signer keys for Teku\Prysm saved to data/configs/signer_keys.yml file.
Proposer config for Teku\Prysm saved to data/configs/proposer_config.json file.

```
#### Options:
- `--validator-index` - The validator index to generate the configuration files.
- `--total-validators` - The total number of validators connected to the web3signer.
- `--db-url` - The database connection address.
- `--web3signer-endpoint` - The endpoint of the web3signer service.
- `--fee-recipient` - The recipient address for MEV & priority fees.
- `--disable-proposal-builder` - Disable proposal builder for Teku and Prysm clients.
- `--output-dir` - The directory to save configuration files. Defaults to ./data/configs.


### 3. Sync Web3Signer config

The command is running by the init container in web3signer pods.
Fetch and decrypt keys for web3signer and store them as keypairs in the output_dir.

Set `DECRYPTION_KEY` env, use value generated by `update-db` command
```bash
# ./key-manager  sync-web3signer
Enter the folder where web3signer keystores will be saved: /data/web3signer
Enter the database connection string, ex. 'postgresql://username:pass@hostname/dbname': postgresql://postgres:postgres@localhost/web3signer

Web3Signer now uses 7 private keys.
```
#### Options:
- `--db-url` - The database connection address.
- `--output-dir` - The folder where Web3Signer keystores will be saved.
- `--decryption-key-env` - The environment variable with the decryption key for private keys in the database.
