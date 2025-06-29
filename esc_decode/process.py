import csv
from collections.abc import Callable, Generator, Iterator
from enum import Enum, unique
from functools import wraps
from typing import TypedDict, TypeVar

import numpy as np
from expression import Error, Ok, Result, effect
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
) -> Generator[Result[ESC_raw_packet, Exception]]:
    """
    https://docs.python.org/3/library/typing.html#annotating-generators-and-coroutines
    """
    for packet_raw in packet_raws:
        miso_list = []
        mosi_list = []
        try:
            for row in packet_raw:
                miso_str = row["MISO"]
                mosi_str = row["MOSI"]
                if not miso_str or not mosi_str:
                    raise ValueError(f"Empty MISO or MOSI value at group {packet_raw}\n")
                miso_list.append(int(miso_str, 16))
                mosi_list.append(int(mosi_str, 16))
            miso_bytes = bytes(miso_list)
            mosi_bytes = bytes(mosi_list)
            yield Ok(ESC_raw_packet(MISOs=miso_bytes, MOSIs=mosi_bytes))
        except Exception as e:
            yield Error(e)


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


class EmptyException(Exception):
    def __init__(self):
        super().__init__()


def ESC_raw_packet_to_ESC_packet(
    rst_raw_packet: Result[ESC_raw_packet, Exception],
    ignore_addrs: set[int] = set(),
) -> Result[ESC_packet, Exception]:
    """
    Convert an ESC_raw_packet to an ESC_packet.

    Section III-Register Descriptions for ESC (EtherCAT Slave Controller), ch6.3
    """
    if rst_raw_packet.is_error():
        return rst_raw_packet
    raw_packet = rst_raw_packet.ok

    m_act = ESC_action.NOP
    try:
        m_act = ESC_action(raw_packet["MOSIs"][0:2][1] & 0b111)
    except ValueError:
        return Error(ValueError("Invalid ESC action in MOSI data"))
    except IndexError:
        return Error(ValueError("Packet too short, may lose data during sampling"))
    m_addr = int.from_bytes(raw_packet["MOSIs"][0:2]) >> 3
    if m_addr in ignore_addrs:
        return Error(EmptyException())

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
            return Error(
                NotImplementedError(f"Unsupported ESC action: {m_act}")
            )  # pragma: no cover

    return Ok(
        ESC_packet(
            m_act=m_act,
            m_addr=m_addr,
            m_data=m_data,
            s_resp_val=s_resp_val,
            al_intp_req_val=al_intp_req_val,
        )
    )


def get_reg_pretty_desc(addr: int, data: bytes) -> str:
    """
    TODO
    support more than 1 addr if packet contains multiple registers
    """
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


def get_packet_desc(rst_packet: Result[ESC_packet, Exception]) -> Result[str, Exception]:
    """
    Get a description of the ESC packet.

    TODO
    use tree structure with expr override will be bettter but more complex
    """
    if rst_packet.is_error():
        return rst_packet

    packet = rst_packet.ok
    out_str = "mcu "
    out_str += f"{packet.m_act.name} "  # action

    match packet.m_act:
        case ESC_action.READ_WAIT:
            out_str += get_reg_pretty_desc(packet.m_addr, packet.s_resp_val)
        case ESC_action.WRITE:
            out_str += get_reg_pretty_desc(packet.m_addr, packet.m_data)
        case _:
            out_str += "(no description)"

    out_str += ", when AL event"
    out_str += f"({ESC_desc_map[0x0220](int.from_bytes(packet.al_intp_req_val))})"
    return Ok(out_str)
