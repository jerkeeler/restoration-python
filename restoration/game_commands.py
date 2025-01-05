import logging
from dataclasses import dataclass

from restoration.consts import FOOTER
from restoration.utils import read_int

logger = logging.getLogger(__name__)


@dataclass
class CommandItem:
    offset_end: int


def parse_command_list(data: bytes, header_end_offset: int) -> list:
    logger.debug(f"Parsing command list starting at {header_end_offset=}")
    offset = data[header_end_offset:].find(FOOTER)
    if offset == -1:
        raise Exception(f"Could not find first footer after offset {header_end_offset}")

    first_foot_end = parse_footer(data, header_end_offset + offset)
    offset = header_end_offset + first_foot_end
    last_index = 1
    command_list = []

    # while True:
    #     if offset == len(data):
    #         break
    #     item = parse_item(data, offset)
    #     last_index += 1
    #     offset = item.offset_end

    return command_list


def parse_footer(data: bytes, offset: int) -> int:
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
    one_fourth_footer_length = read_int(data, offset)
    offset += 4
    end_offset = offset + 4 * one_fourth_footer_length
    late = data[offset:end_offset]
    return end_offset


def parse_item(data: bytes, offset: int) -> CommandItem:
    return CommandItem(offset_end=offset)
