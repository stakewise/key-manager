from dataclasses import dataclass

MAINNET = 'mainnet'
GOERLI = 'goerli'
GNOSIS = 'gnosis'

# aliases
PRATER = 'prater'


@dataclass
class NetworkConfig:
    MAX_KEYS_PER_VALIDATOR: int
    IS_POA: bool


NETWORKS = {
    MAINNET: NetworkConfig(
        MAX_KEYS_PER_VALIDATOR=100,
        IS_POA=True,
    ),
    GOERLI: NetworkConfig(
        MAX_KEYS_PER_VALIDATOR=100,
        IS_POA=False,
    ),
    GNOSIS: NetworkConfig(
        MAX_KEYS_PER_VALIDATOR=100,
        IS_POA=True,
    ),
}

# Alias
NETWORKS[PRATER] = NETWORKS[GOERLI]

AVAILABLE_NETWORKS = list(NETWORKS.keys())
