import json
import time
from dataclasses import dataclass
from functools import cached_property
from os import makedirs, path
from typing import NewType

import click
import milagro_bls_binding as bls
from eth_typing import HexAddress, HexStr
from py_ecc.bls import G2ProofOfPossession
from staking_deposit.key_handling.key_derivation.mnemonic import get_seed
from staking_deposit.key_handling.key_derivation.path import path_to_nodes
from staking_deposit.key_handling.key_derivation.tree import (
    derive_child_SK,
    derive_master_SK,
)
from staking_deposit.key_handling.keystore import Keystore, ScryptKeystore
from sw_utils import ExtendedAsyncBeacon, get_eth1_withdrawal_credentials
from sw_utils.signing import (
    DepositData,
    DepositMessage,
    compute_deposit_domain,
    compute_signing_root,
)
from sw_utils.typings import Bytes32
from web3 import Web3

from key_manager import KEY_MANAGER_VERSION
from key_manager.password import get_or_create_password_file
from key_manager.settings import NETWORKS

# Set path as EIP-2334 format
# https://eips.ethereum.org/EIPS/eip-2334
PURPOSE = '12381'
COIN_TYPE = '3600'

w3 = Web3()

BLSPrivkey = NewType('BLSPrivkey', int)


@dataclass
class Credential:
    private_key: BLSPrivkey
    path: str
    network: str
    vault: HexAddress

    @cached_property
    def public_key(self) -> HexStr:
        return w3.to_hex(G2ProofOfPossession.SkToPk(self.private_key))

    @cached_property
    def private_key_bytes(self) -> bytes:
        return self.private_key.to_bytes(32, 'big')

    @cached_property
    def amount(self) -> int:
        return NETWORKS[self.network].DEPOSIT_AMOUNT_GWEI

    @cached_property
    def withdrawal_credentials(self) -> Bytes32:
        return get_eth1_withdrawal_credentials(self.vault)

    def encrypt_signing_keystore(self, password: str) -> Keystore:
        return ScryptKeystore.encrypt(
            secret=self.private_key_bytes, password=password, path=self.path
        )

    def save_signing_keystore(self, password: str, folder: str) -> str:
        keystore = self.encrypt_signing_keystore(password)
        filefolder = path.join(
            folder, f'keystore-{keystore.path.replace("/", "_")}-{time.time()}.json'
        )
        keystore.save(filefolder)
        return filefolder

    @property
    def deposit_message(self) -> DepositMessage:
        return DepositMessage(
            pubkey=Web3.to_bytes(hexstr=self.public_key),
            withdrawal_credentials=self.withdrawal_credentials,
            amount=self.amount,
        )

    @property
    def signed_deposit(self) -> DepositData:
        domain = compute_deposit_domain(fork_version=NETWORKS[self.network].GENESIS_FORK_VERSION)
        signing_root = compute_signing_root(self.deposit_message, domain)
        signed_deposit = DepositData(
            **self.deposit_message.as_dict(),
            # pylint: disable-next=no-member
            signature=bls.Sign(self.private_key_bytes, signing_root),
        )
        return signed_deposit

    @property
    def deposit_datum_dict(self) -> dict[str, bytes]:
        signed_deposit_datum = self.signed_deposit
        datum_dict = signed_deposit_datum.as_dict()
        datum_dict.update({'deposit_message_root': self.deposit_message.hash_tree_root})
        datum_dict.update({'deposit_data_root': signed_deposit_datum.hash_tree_root})
        datum_dict.update({'fork_version': NETWORKS[self.network].GENESIS_FORK_VERSION})
        datum_dict.update({'network_name': self.network})
        datum_dict.update({'deposit_cli_version': KEY_MANAGER_VERSION})
        return datum_dict


async def generate_credentials(
    network: str,
    vault: HexAddress,
    mnemonic: str,
    count: int,
    used_keys: list[HexStr],
    consensus_client: ExtendedAsyncBeacon,
) -> list[Credential]:

    credentials: dict[HexStr, Credential] = {}
    with click.progressbar(
        length=count,
        label='Creating validator keys:\t\t',
        show_percent=False,
        show_pos=True,
    ) as bar:
        from_index = 0
        while len(credentials) < count:
            curr_progress = len(credentials)
            chunk_size = min(100, count - curr_progress)

            # generate keys in chunks
            public_keys_chunk: list[HexStr] = []
            while len(public_keys_chunk) != chunk_size:
                credential = _generate_credential(network, vault, mnemonic, from_index)

                if credential.public_key not in used_keys:
                    credentials[credential.public_key] = credential
                    public_keys_chunk.append(credential.public_key)

                # increase index for generating other keys
                from_index += 1

            # remove keys that were already registered in beacon chain
            result = (await consensus_client.get_validators_by_ids(public_keys_chunk))['data']
            registered_validators = [item['validator']['pubkey'] for item in result]

            for registered_validator in registered_validators:
                credentials.pop(registered_validator, None)

            bar.update(len(credentials) - curr_progress)

    return list(credentials.values())


def _generate_credential(
    network: str, vault: HexAddress, mnemonic: str, from_index: int
) -> Credential:
    """Returns the signing key of the mnemonic at a specific index."""
    seed = get_seed(mnemonic=mnemonic, password='')  # nosec
    private_key = BLSPrivkey(derive_master_SK(seed))
    signing_key_path = f'm/{PURPOSE}/{COIN_TYPE}/{from_index}/0/0'
    nodes = path_to_nodes(signing_key_path)

    for node in nodes:
        private_key = BLSPrivkey(derive_child_SK(parent_SK=private_key, index=node))

    return Credential(private_key=private_key, path=signing_key_path, network=network, vault=vault)


def export_deposit_data_json(credentials: list[Credential], filename: str) -> str:
    with click.progressbar(
        credentials, label='Generating deposit data json\t\t', show_percent=False, show_pos=True
    ) as _credentials:
        deposit_data = [cred.deposit_datum_dict for cred in _credentials]
    makedirs(path.dirname(path.abspath(filename)), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(deposit_data, f, default=lambda x: x.hex())
    return filename


def export_keystores(credentials: list[Credential], keystores_dir: str, password_file: str) -> None:
    makedirs(path.abspath(keystores_dir), exist_ok=True)
    password = get_or_create_password_file(password_file)
    with click.progressbar(
        credentials,
        label='Exporting validator keystores\t\t',
        show_percent=False,
        show_pos=True,
    ) as _credentials:
        for credential in _credentials:
            credential.save_signing_keystore(password=password, folder=keystores_dir)
