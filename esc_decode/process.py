import csv
from collections.abc import Callable, Generator, Iterator
from enum import Enum, unique
from functools import wraps
from typing import TypedDict, TypeVar

import numpy as np
from expression import Nothing, Option, Result, Some, effect
from pydantic import BaseModel
from termcolor import colored

from esc_decode.reg_desc import REG_ADDR_TO_NAME, ESC_desc_map


class RowDict(TypedDict):
    MISO: str
    MOSI: str
    time: np.timedelta64


def row_stream(file: str):
    with open(file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row.pop("Id", None)
            row["MISO"] = row.pop("0:SPI: MISO data")
            row["MOSI"] = row.pop("0:SPI: MOSI data")
            row["time"] = np.timedelta64(int(float(row.pop("Time[ns]"))), "ns")
            yield row


def aggregate_stream(rows: Iterator[RowDict], threshold=4) -> Iterator[list[RowDict]]:
    group = []
    last_time = None
    for row in rows:
        if not group:
            group.append(row)
            last_time = row["time"]
        elif row["time"] - last_time <= np.timedelta64(threshold, "us"):
            group.append(row)
        else:
            yield group
            group = [row]
        last_time = row["time"]
    if group:
        yield group


class ESC_raw_packet(TypedDict):
    MISOs: bytes
    MOSIs: bytes


# @effect.option[ESC_raw_packet]()
def packet_transform(
    packet_raws: Iterator[list[RowDict]],
) -> Generator[Option[ESC_raw_packet]]:
    """
    https://docs.python.org/3/library/typing.html#annotating-generators-and-coroutines
    """
    for packet_raw in packet_raws:
        miso_bytes = bytes(int(row["MISO"], 16) for row in packet_raw)
        mosi_bytes = bytes(int(row["MOSI"], 16) for row in packet_raw)
        yield Some(ESC_raw_packet(MISOs=miso_bytes, MOSIs=mosi_bytes))


T = TypeVar("T")
U = TypeVar("U")


def make_gen(
    fn: Callable[[T], U],
) -> Callable[[Generator[T, None, None]], Generator[U, None, None]]:
    @wraps(fn)
    def wrapper(gen: Generator[T, None, None]) -> Generator[U, None, None]:
        for item in gen:
            yield fn(item)

    return wrapper


@unique
class ESC_action(Enum):
    NOP = 0x0
    READ = 0x2
    READ_WAIT = 0x3
    WRITE = 0x4
    ADDR_EXT = 0x6


class ESC_packet(BaseModel):
    m_act: ESC_action
    m_addr: int
    m_data: bytes
    s_resp_val: bytes
    al_intp_req_val: bytes


def endian_invert(bytes_in: bytes) -> bytes:
    return bytes_in[::-1]


def ESC_raw_packet_to_ESC_packet(
    opt_raw_packet: Option[ESC_raw_packet],
) -> Option[ESC_packet]:
    """
    Convert an ESC_raw_packet to an ESC_packet.

    Section III-Register Descriptions for ESC (EtherCAT Slave Controller), ch6.3
    """
    if opt_raw_packet.is_none():
        return Nothing
    raw_packet = opt_raw_packet.value

    m_act = ESC_action.NOP
    try:
        m_act = ESC_action(raw_packet["MOSIs"][0:2][1] & 0b111)
    except ValueError:
        return Nothing
    m_addr = int.from_bytes(raw_packet["MOSIs"][0:2]) >> 3

    m_data = b""
    s_resp_val = b""
    al_intp_req_val = endian_invert(raw_packet["MISOs"][0:2])
    match m_act:
        case ESC_action.READ:
            # m_data = endian_invert(raw_packet["MOSIs"][2:])
            s_resp_val = endian_invert(raw_packet["MISOs"][2:])
        case ESC_action.READ_WAIT:
            # m_data = endian_invert(raw_packet["MOSIs"][3:])
            s_resp_val = endian_invert(raw_packet["MISOs"][3:])
        case ESC_action.WRITE:
            m_data = endian_invert(raw_packet["MOSIs"][2:])
        case _:
            return Nothing

    return Some(
        ESC_packet(
            m_act=m_act,
            m_addr=m_addr,
            m_data=m_data,
            s_resp_val=s_resp_val,
            al_intp_req_val=al_intp_req_val,
        )
    )


def get_reg_pretty_desc(addr: int, data: bytes) -> str:
    out_str = f"reg:{hex(addr)}"
    if addr not in REG_ADDR_TO_NAME:
        out_str += colored("(unknown register)", "red")
        return out_str
    out_str += f"({REG_ADDR_TO_NAME[addr]})"

    if data == b"":
        return out_str

    out_str += f", data:0x{data.hex()}"
    if addr in ESC_desc_map:
        desc_func = ESC_desc_map[addr]
        out_str += f"({desc_func(int.from_bytes(data))})"
    else:
        out_str += colored("(no description)", "red")
    return out_str


def get_packet_desc(opt_packet: Option[ESC_packet]) -> Option[str]:
    """
    Get a description of the ESC packet.

    TODO
    use tree structure with expr override will be bettter but more complex
    """
    if opt_packet.is_none():
        return Nothing

    packet = opt_packet.value
    out_str = "mcu "
    out_str += f"{packet.m_act.name}"  # action

    match packet.m_act:
        case ESC_action.READ_WAIT:
            out_str += get_reg_pretty_desc(packet.m_addr, packet.s_resp_val)
        case ESC_action.WRITE:
            out_str += get_reg_pretty_desc(packet.m_addr, packet.m_data)
        case _:
            out_str += "(no description)"

    out_str += ", when AL event"
    out_str += f"({ESC_desc_map[0x0220](int.from_bytes(packet.al_intp_req_val))})"
    return Some(out_str)
