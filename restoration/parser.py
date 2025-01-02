import gzip
import io
import logging
import struct
import zlib

logger = logging.getLogger(__name__)

OUTER_HIERARCHY_START_OFFSET = 255


def decompressl33t(stream: io.BufferedReader | gzip.GzipFile) -> io.BytesIO:
    # Read the first 4 bytes of the stream and check if it is l33t encoded
    header = stream.read(4)
    if header != b"l33t":
        raise ValueError("Invalid header. Expecting 'l33t'")

    decompress = zlib.decompressobj()
    # Read the length of the compressed data, need to read so that the rest can be
    # decompressed with one read operation
    struct.unpack("<i", stream.read(4))[0]
    return io.BytesIO(decompress.decompress(stream.read()))


def parse_rec(stream: io.BufferedReader | gzip.GzipFile) -> None:
    decompressed_data = decompressl33t(stream)
    decompressed_data.seek(OUTER_HIERARCHY_START_OFFSET)
    logger.debug(decompressed_data.read(4).decode("utf-8"))
