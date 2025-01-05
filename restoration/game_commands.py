import logging
from dataclasses import dataclass, field

from restoration.consts import FOOTER
from restoration.utils import read_int32, read_short

logger = logging.getLogger(__name__)


@dataclass
class CommandItem:
    offset_end: int


@dataclass
class CommandList:
    offset_end: int
    commands: list[CommandItem] = field(default_factory=list)


def parse_command_list(data: bytes, header_end_offset: int) -> list[CommandList]:
    logger.debug(f"Parsing command list starting at {header_end_offset=}")
    offset = data[header_end_offset:].find(FOOTER)
    logger.debug(f"Header offset = {offset}")
    if offset == -1:
        raise Exception(f"Could not find first footer after offset {header_end_offset}")

    first_foot_end = parse_footer(data, header_end_offset + offset)
    offset = first_foot_end + 5
    last_index = 1
    command_list: list[CommandList] = []

    while True:
        if offset == len(data):
            break
        item = parse_item(data, offset)
        last_index += 1
        offset = item.offset_end

    return command_list


def parse_footer(data: bytes, offset: int) -> int:
    logger.debug(f"footer start {offset=}")
    early = data[offset : offset + 10]
    extra_byte_count = data[offset]
    offset += 1
    extra_byte_numbers = [data[offset + i] for i in range(extra_byte_count)]
    if extra_byte_count > 0:
        logger.debug(f"footer has {extra_byte_count} extra bytes: {extra_byte_numbers}")
    offset += extra_byte_count

    unk = data[offset]
    if unk != 1:
        raise Exception(f"Expected unk to equal 1 at {offset=} by got {unk=}")

    offset += 9
    one_fourth_footer_length = read_short(data, offset)
    logger.debug(f"{one_fourth_footer_length=}")
    offset += 4
    end_offset = offset + 4 * one_fourth_footer_length
    late = data[offset:end_offset]
    return end_offset


def parse_item(data: bytes, offset: int) -> CommandList:
    """
    Parses a command item, which is actually a list of commands. The first int is a bit mask. Valid values:
    1
    32
    64
    128
    """
    logger.debug(f"Parsing item at {offset=}")
    entry_type = read_short(data, offset)
    offset += 4
    early_byte = data[offset]
    offset += 1

    # Raise exceptions if the bit mask is not valid
    logger.debug(f"{offset=} {entry_type}")
    if entry_type & 225 != entry_type:
        raise Exception(f"Bad entry type, masking to 225 doesn't work for {entry_type}")
    # 32 + 64 together makes no sense
    if entry_type & 96 == 96:
        raise Exception("96 entry type doesn't make sense for entry type")

    if entry_type & 1 == 0:
        offset += 4
    else:
        offset += 1

    commands: list[CommandItem] = []

    # Handle both kinds of commands handling data, 32 and 64
    if entry_type & 96:
        num_items = 0
        if entry_type & 32:
            num_items = data[offset]
            offset += 1
        elif entry_type & 64:
            num_items = read_short(data, offset)
            offset += 4

        for _ in range(num_items):
            # Parse commands
            command = parse_game_command(data, offset)
            offset = command.offset_end
            commands.append(command)

    # Handle unit selection change
    selected_units: list = []
    if entry_type & 128:
        num_items = data[offset]
        offset += 1
        for _ in range(num_items):
            selected_units.append(read_short(data, offset))
            offset += 4

    footer_end_offset = parse_footer(data, offset)
    offset = footer_end_offset
    entry_index = read_short(data, offset)
    offset += 4
    finalByte = data[offset]
    offset += 1

    return CommandList(offset_end=offset, commands=commands)


def parse_game_command(data, offset) -> CommandItem:
    command_type = data[offset + 1]
    ten_bytes_offset = offset
    offset += 1
    if command_type == 14:
        offset += 20
    else:
        offset += 8

    three = read_short(data, offset)
    if three != 3:
        raise Exception("Expecting three in parsing game command!")
    offset += 4

    player_id = -1
    if command_type == 19:
        player_id = data[ten_bytes_offset + 7]
        offset += 4
    else:
        one = read_short(data, offset)
        if one != 1:
            raise Exception("Expecting one")
        offset += 4
        player_id = read_short(data, offset)
        if player_id > 12:
            raise Exception("Player id must be 12 or less")
        offset += 4
    offset += 4
    num_units = read_short(data, offset)
    offset += 4

    source_units: list[int] = []
    for _ in range(num_units):
        source_units.append(read_short(data, offset))
        offset += 4

    num_vectors = read_short(data, offset)
    offset += 4
    source_vectors: list[int] = []
    for _ in range(num_vectors):
        # TODO: parse vectors
        offset += 12

    num_pre_argument_bytes = 13 + read_short(data, offset)
    offset += 4
    pre_argument_bytes: list[int] = []
    for idx in range(num_pre_argument_bytes):
        pre_argument_bytes.append(data[offset + idx])
    offset += num_pre_argument_bytes

    # Refiners
    raise Exception(f"Need to add refiner for command_type {command_type}")

    return CommandItem(offset)
