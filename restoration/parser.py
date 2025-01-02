import gzip
import io
import logging
import string
import struct
import zlib
from dataclasses import dataclass, field
from functools import cached_property

logger = logging.getLogger(__name__)

OUTER_HIERARCHY_START_OFFSET = 257
DATA_OFFSET = 6
UPPERCASE_ASSCII = set(bytes(string.ascii_uppercase, "utf-8"))


@dataclass
class Node:
    token: str
    offset: int
    size: int
    parsed: bool = False
    parent: "Node | None" = None
    children: list["Node"] = field(default_factory=list)

    @cached_property
    def end_offset(self):
        return self.offset + self.size + DATA_OFFSET

    @cached_property
    def path(self) -> str:
        if self.parent is None:
            return self.token
        return f"{self.parent.path}/{self.token}"

    def __str__(self) -> str:
        return (
            f"{self.path} -- offset={self.offset}, end_offset={self.end_offset} "
            f"size={self.size}, children={len(self.children)}"
        )


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


def parse_rec(stream: io.BufferedReader | gzip.GzipFile) -> tuple[io.BytesIO, Node]:
    decompressed_data = decompressl33t(stream)
    decompressed_data.seek(OUTER_HIERARCHY_START_OFFSET)
    bs = decompressed_data.read(2)
    two_letter_code = bs.decode("utf-8")
    data_len = struct.unpack("<H", decompressed_data.read(2))[0]
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
    return decompressed_data, root_node


def recursive_create_tree(
    parent_node: Node,
    decompressed_data: io.BytesIO,
) -> None:
    """
    Recursively build up the metadata tree using a breadth first search approach.
    """
    logger.debug(
        f"Searching for children for {parent_node.token} at: {parent_node.offset}"
    )
    decompressed_data.seek(parent_node.offset)
    # Skip the first two bytes, since those are the node token
    position = parent_node.offset + 2
    while position < parent_node.end_offset:
        next_node_loc = find_two_letter_seq(
            decompressed_data,
            offset=position,
            upper_bound=parent_node.end_offset,
        )
        if next_node_loc == -1:
            break

        decompressed_data.seek(next_node_loc)
        token = decompressed_data.read(2).decode("utf-8")
        size = struct.unpack("<H", decompressed_data.read(2))[0]
        node = Node(
            token=token,
            offset=next_node_loc,
            size=size,
            parent=parent_node,
        )
        decompressed_data.seek(node.end_offset)
        parent_node.children.append(node)
        position = node.end_offset

    for child in parent_node.children:
        recursive_create_tree(child, decompressed_data)


def find_two_letter_seq(
    data: io.BytesIO,
    offset: int = 0,
    upper_bound: int | None = None,
) -> int:
    """
    Searches for the sequence b"<Uppercase ASCII><Uppercase ASCII>". Moves the reads to offset before
    searching and moves it back to offset once done searching.
    """
    data.seek(offset)
    position = offset

    while True:
        if upper_bound is not None and position >= upper_bound:
            break

        data.seek(position)
        # Note, there's a weird thing with python that if you have a byte string with
        # a single byte like b'A', it will be treated as an integer. But if you have
        # a byte string with two bytes like b'AB', it will be treated as a byte string.
        # It's very annoying. So you could change this to read a new character one at
        # a time, it would be more efficient, but I'm not annoyed to figure it out.
        byte1, byte2 = data.read(2)
        if byte1 in UPPERCASE_ASSCII and byte2 in UPPERCASE_ASSCII:
            data.seek(offset)
            return position

        position += 1

    logger.debug(
        f"Could not find a two letter sequence starting at {offset=}, {upper_bound=}"
    )
    data.seek(offset)
    return -1


def get_nodes(root_node: Node, path: list[str]) -> list[Node]:
    if not path:
        return [root_node]

    nodes = []
    for child in root_node.children:
        if child.token == path[0]:
            nodes.extend(get_nodes(child, path[1:]))

    return nodes
