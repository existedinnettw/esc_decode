import pytest  # noqa: F401
from expression import pipe

from esc_decode.process import (
    ESC_raw_packet_to_ESC_packet,
    aggregate_stream,
    get_packet_desc,
    make_gen,
    packet_transform,
    row_stream,
)
from esc_decode.reg_desc import ESC_desc_map


def test_aggregate():
    file = "tests/data/decoder--250531-232808.csv"
    for packet_raw in aggregate_stream(row_stream(file)):
        # print("packet_raw:")
        for per_raw_byte in packet_raw:
            pass
            # print(per_raw_byte)


def test_packet_raw_create():
    file = "tests/data/decoder--250531-232808.csv"
    for packet in pipe(file, row_stream, aggregate_stream, packet_transform):
        if packet.is_some():
            print("packet:")
            print(packet.value)
        else:
            print("failed")


def test_packet_create():
    file = "tests/data/decoder--250531-232808.csv"
    for packet in pipe(
        file, row_stream, aggregate_stream, packet_transform, make_gen(ESC_raw_packet_to_ESC_packet)
    ):
        if packet.is_some():
            print("packet:")
            print(packet.value)
        else:
            print("failed")


def test_desc():
    print(ESC_desc_map[0x0138](0x1D))


def test_packet_desc():
    file = "tests/data/decoder--250531-232808.csv"
    for opt_packet_str in pipe(
        file,
        row_stream,
        aggregate_stream,
        packet_transform,
        make_gen(ESC_raw_packet_to_ESC_packet),
        make_gen(get_packet_desc),
    ):
        if not opt_packet_str.is_some():
            continue

        print(opt_packet_str.value)
