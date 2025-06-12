import argparse
import sys

from expression import Result, pipe
from termcolor import colored

from esc_decode.process import (
    ESC_raw_packet_to_ESC_packet,
    aggregate_stream,
    get_packet_desc,
    make_gen,
    packet_transform,
    row_stream,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode ESC commands from a file.")
    parser.add_argument(
        "input_file", type=str, help="Path to the input file containing ESC commands."
    )
    parser.add_argument(
        "-th",
        "--threshold",
        type=int,
        default=10,
        help="Time threshold in us for aggregating packets (default: 10 us).",
    )

    def auto_int(x):
        return int(x, 0)

    parser.add_argument(
        "-i",
        "--ignore_addrs",
        nargs="+",
        type=auto_int,
        default=set(),
        help="MOSI register address to be ignore decoding (e.g., 0x0000, 0x0220...).",
    )

    args = parser.parse_args()

    def timed_aggregate_stream(rows):
        return aggregate_stream(rows, args.threshold)

    def new_ESC_raw_packet_to_ESC_packet(x):
        return ESC_raw_packet_to_ESC_packet(x, ignore_addrs=args.ignore_addrs)

    for rst_packet_str in pipe(
        args.input_file,
        row_stream,
        timed_aggregate_stream,
        packet_transform,
        make_gen(new_ESC_raw_packet_to_ESC_packet),
        make_gen(get_packet_desc),
    ):
        rst_packet_str: Result[str, Exception]
        if rst_packet_str.is_error():
            if str(rst_packet_str.error) != "":
                print(colored(f"Failed to decode packet. Reason: {rst_packet_str.error}", "red"))
            continue

        print(rst_packet_str.ok)
    sys.exit(0)
