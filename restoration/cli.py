import gzip
import logging

import click

from restoration.parser import parse_rec


@click.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--is-gzip",
    is_flag=True,
    help="Decompress the file using gzip before processing",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def cli(filepath: str, is_gzip: bool, verbose: bool) -> None:
    if verbose:
        click.echo("Verbose logging enabled")
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    # Ignoring types because we are purposefully overloading this variable to make the code nicer
    o = open  # type: ignore
    if is_gzip:
        o = gzip.open  # type: ignore
    with o(filepath, "rb") as file:
        parse_rec(file)
    click.echo("Rec parsed!")


if __name__ == "__main__":
    cli()
