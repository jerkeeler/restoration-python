import gzip
import io
import struct
import typing
import zlib

import click


def decompressl33t(stream: typing.BinaryIO) -> typing.BinaryIO:
    # Read the first 4 bytes of the stream and check if it is l33t encoded
    header = stream.read(4)
    if header != b"l33t":
        raise ValueError("Invalid header. Expecting 'l33t'")

    decompress = zlib.decompressobj()
    # Read the length of the compressed data, need to read so that the rest can be
    # decompressed with one read operation
    struct.unpack("<i", stream.read(4))[0]
    return io.BytesIO(decompress.decompress(stream.read()))


@click.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--is-gzip",
    is_flag=True,
    help="Decompress the file using gzip before processing",
)
def cli(filepath: str, is_gzip: bool):
    o = open
    if is_gzip:
        o = gzip.open
    with o(filepath, "rb") as file:
        data = decompressl33t(file)
        click.echo("Decompressed!")


if __name__ == "__main__":
    cli()
