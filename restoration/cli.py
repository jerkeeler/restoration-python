import gzip
import json
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
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option("-o", "--output", type=click.Path(writable=True), help="Save the output as a json file")
@click.option("-q", "--quiet", is_flag=True, help="Don't show the output")
def cli(filepath: str, is_gzip: bool, verbose: bool, output: str, quiet: bool) -> None:

    if verbose:
        click.echo("Verbose logging enabled")
        logging.basicConfig(level=logging.DEBUG)

    # Ignoring types because we are purposefully overloading this variable to make the code nicer
    o = open  # type: ignore
    if is_gzip:
        o = gzip.open  # type: ignore
    with o(filepath, "rb") as file:
        replay = parse_rec(file)

    if not quiet:
        json_str = replay.to_json()
        click.echo(json_str)

    if output:
        with open(output, "w") as f:
            f.write(replay.to_json())


if __name__ == "__main__":
    cli()
