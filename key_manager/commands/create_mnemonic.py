import click

from key_manager.language import LANGUAGES, create_new_mnemonic


@click.option(
    '--language',
    default='english',
    prompt='Choose your mnemonic language',
    type=click.Choice(
        LANGUAGES,
        case_sensitive=False,
    ),
)
@click.option(
    '--no-verify',
    is_flag=True,
    help='Skips mnemonic verification when provided.',
)
@click.command(help='Creates the mnemonic used to derive validator keys.')
def create_mnemonic(language: str, no_verify: bool) -> None:
    if not language:
        language = click.prompt(
            'Choose your mnemonic language',
            default='english',
            type=click.Choice(LANGUAGES, case_sensitive=False),
        )
    create_new_mnemonic(language, skip_test=no_verify)
