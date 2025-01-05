import gzip
import io
import logging
import string
import struct
import zlib
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Callable

from restoration.consts import (
    MAX_SCAN_LENGTH,
    OUTER_HIERARCHY_START_OFFSET,
    UPPERCASE_ASSCII,
)
from restoration.enums import KeyType
from restoration.types import PROFILE_KEY_VALUE_TPYES, Node
from restoration.xceptions import NodeNotFound

logger = logging.getLogger(__name__)


def decompressl33t(stream: io.BufferedReader | gzip.GzipFile) -> bytes:
    # Read the first 4 bytes of the stream and check if it is l33t encoded
    header = stream.read(4)
    if header != b"l33t":
        raise ValueError("Invalid header. Expecting 'l33t'")

    decompress = zlib.decompressobj()
    # Read the length of the compressed data, need to read so that the rest can be
    # decompressed with one read operation
    struct.unpack("<i", stream.read(4))[0]
    return decompress.decompress(stream.read())


def parse_rec(stream: io.BufferedReader | gzip.GzipFile) -> tuple[bytes, Node]:
    decompressed_data = decompressl33t(stream)
    position = OUTER_HIERARCHY_START_OFFSET
    two_letter_code = decompressed_data[position : position + 2].decode("utf-8")
    position += 2
    data_len = struct.unpack("<H", decompressed_data[position : position + 2])[0]
    position += 2

    # 6 bytes of padding for no reason? Don't think this is needed
    # decompressed_data.read(DATA_OFFSET)
    root_node = Node(
        token=two_letter_code,
        offset=OUTER_HIERARCHY_START_OFFSET,
        size=data_len,
    )
    logger.debug(two_letter_code)
    logger.debug(data_len)
    recursive_create_tree(root_node, decompressed_data)
    root_node.print()
    read_build_string(root_node, decompressed_data)
    parse_profile_keys(root_node, decompressed_data)
    return decompressed_data, root_node


def read_int(data: bytes, offset: int) -> int:
    return struct.unpack("<H", data[offset : offset + 2])[0]


def read_bool(data: bytes, offset: int) -> bool:
    return struct.unpack("<?", data[offset : offset + 1])[0]


def recursive_create_tree(
    parent_node: Node,
    decompressed_data: bytes,
) -> None:
    """
    Recursively build up the metadata tree using a breadth first search approach.
    """
    # Skip the first two bytes to start the children search since those are the node token
    position = parent_node.offset + 2
    while position < parent_node.end_offset:
        next_node_loc = find_two_letter_seq(
            decompressed_data,
            offset=position,
            upper_bound=parent_node.end_offset,
        )
        if next_node_loc == -1:
            break

        position = next_node_loc
        token = decompressed_data[position : position + 2].decode("utf-8")
        position += 2
        size = read_int(decompressed_data, position)
        position += 2

        node = Node(
            token=token,
            offset=next_node_loc,
            size=size,
            parent=parent_node,
        )
        parent_node.children.append(node)
        position = node.end_offset

    for child in parent_node.children:
        recursive_create_tree(child, decompressed_data)


def find_two_letter_seq(
    data: bytes,
    offset: int = 0,
    upper_bound: int | None = None,
) -> int:
    """
    Searches for the sequence b"<Uppercase ASCII><Uppercase ASCII>". Moves the reads to offset before
    searching and moves it back to offset once done searching.
    """
    if upper_bound is None:
        upper_bound = len(data)

    if not data or upper_bound - offset < 2:
        return -1

    position = offset
    byte1 = data[position]
    byte2 = data[position + 1]

    while True:
        if upper_bound is not None and position >= upper_bound:
            break

        # Note, there's a weird thing with python that if you have a byte string with
        # a single byte like b'A', it will be treated as an integer. But if you have
        # a byte string with two bytes like b'AB', it will be treated as a byte string.
        # It's very annoying. So you could change this to read a new character one at
        # a time, it would be more efficient, but I'm not annoyed to figure it out.
        if byte1 in UPPERCASE_ASSCII and byte2 in UPPERCASE_ASSCII:
            return position

        position += 1

        if position + 1 > len(data) - 1:
            break
        byte1 = byte2
        byte2 = data[position + 1]

        if position > offset + MAX_SCAN_LENGTH:
            # If we don't find a two letter sequence within 50 bytes, then we're probably in a pad position and should
            # exit out
            logger.warning(f"Could not find a two letter sequence at {offset=}")
            break

    return -1


def read_string(data: bytes, offset: int) -> tuple[str, int]:
    """
    Reads the utf-16 little endian encoded at the given offset. Strings are enocde such that the first 2 bytes
    are an unsigned integer indicating the number of characters in the string. The next 2 bytes are null padding.
    Then the string follows. Since the strings are unicode enocode each character takes up 2 bytes.
    For example a string might look like:
    \x02\x00\x00\x00H\x00e\x00l\x00l\x00o\x00

    Returns the string and the index directly after the string.
    """
    num_chars = read_int(data, offset)
    start_of_string = offset + 4  # offset + 2 bytes for int + 2 bytes of padding
    end_of_string = start_of_string + num_chars * 2
    # Characters are defined with 2 bytes using utf-16 little endian encoding, so multiple by 2 to get the number
    # of bytes to read
    raw_string = data[start_of_string:end_of_string]
    s = raw_string.decode("utf-16-le")
    return s, end_of_string


def read_build_string(root_node: Node, data: bytes) -> str:
    """
    Finds the FH node, then reads the string at the FH node offset to get the build information. There is other
    information in the FH node, but I don't know what it is.
    """
    children = root_node.get_children(["FH"])
    if not children:
        raise NodeNotFound("Could not find FH node! No build string!")
    if len(children) > 1:
        logger.warning("Found multiple FH nodes! Using the first one.")
    fh_node = children[0]
    position = fh_node.offset + 6  # skip the token and data length (4) + 2 null padding bytes
    s, _ = read_string(data, position)
    logger.debug(f"build_string={s}")
    return s


def parse_string(data: bytes, position: int, keyname: str) -> tuple[str, int]:
    read_pos = position + 2
    # There is some off by one (byte?) when r
    if keyname in {"gamename"}:
        read_pos = position
    s, new_position = read_string(data, read_pos)
    position = new_position
    if keyname in {"gamename"}:
        position = new_position + 2  # Skip 2 null padding bytes
    return s, position


def parse_integer(data: bytes, position: int, _: str) -> tuple[int, int]:
    i = read_int(data, position + 2)  # Skip 2 null padding bytes
    position = position + 6  # Skip 2 for the int and 4 null padding bytes
    return i, position


def parse_int16(data: bytes, position: int, _: str) -> tuple[int, int]:
    i = read_int(data, position + 2)  # Skip 2 null padding bytes
    position = position + 4  # Skip 2 for the int and 2 null padding bytes
    return i, position


def parse_boolean(data: bytes, position: int, _: str) -> tuple[bool, int]:
    b = read_bool(data, position)
    position = position + 3  # Skip 1 for the bool and 2 null padding bytes
    return b, position


def parse_gamesyncstate(_: bytes, position: int, __: str) -> tuple[None, int]:
    return None, position + 10


KETYPE_PARSE_MAP: dict[KeyType, Callable[[bytes, int, str], tuple[PROFILE_KEY_VALUE_TPYES, int]]] = {
    KeyType.string: parse_string,
    KeyType.uint32: parse_integer,
    KeyType.int32: parse_integer,
    KeyType.int16: parse_int16,
    KeyType.boolean: parse_boolean,
    KeyType.gamesyncstate: parse_gamesyncstate,
}


def parse_profile_keys(root_node: Node, data: bytes) -> None:
    children = root_node.get_children(["MP", "ST"])
    if not children:
        raise NodeNotFound("Could not find ST node! No profile keys!")
    if len(children) > 1:
        logger.warning("Found multiple ST nodes! Using the first one.")
    st_node = children[0]
    # Skip the token and data length (4) + 6 null padding bytes
    position = st_node.offset + 10
    num_keys = read_int(data, position)
    logger.debug(f"{num_keys=}")
    position += 4  # Position + 2 for the num_keys read and skip 2 null padding bytes
    profile_keys: dict[str, PROFILE_KEY_VALUE_TPYES] = {}
    for _ in range(num_keys):
        keyname, next_position = read_string(data, position)
        keytype = KeyType(read_int(data, next_position))
        logger.debug(f"{keyname=}, {keytype=}, {position=}, {next_position=}")
        position = next_position + 2  # Skip the keytype and 2 null padding bytes
        parse_func = KETYPE_PARSE_MAP.get(keytype)
        if not parse_func:
            raise ValueError(f"No parser for keytype: {keytype}")
        keydata, position = parse_func(data, position, keyname)
        profile_keys[keyname] = keydata
