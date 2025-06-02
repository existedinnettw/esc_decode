import argparse

from expression import pipe
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
        "--threshold",
        type=int,
        default=4,
        help="Time threshold in us for aggregating packets (default: 4 us).",
    )

    args = parser.parse_args()

    def timed_aggregate_stream(rows):
        return aggregate_stream(rows, args.threshold)

    for opt_packet_str in pipe(
        args.input_file,
        row_stream,
        timed_aggregate_stream,
        packet_transform,
        make_gen(ESC_raw_packet_to_ESC_packet),
        make_gen(get_packet_desc),
    ):
        if not opt_packet_str.is_some():
            print(colored("Failed to decode packet."), "red")
            continue

        print(opt_packet_str.value)
