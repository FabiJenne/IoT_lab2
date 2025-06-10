from __future__ import annotations

import time
from argparse import ArgumentParser
from typing import Any, cast

import numpy as np

import zmq


def recv_array(
    socket: zmq.Socket, flags: int = 0, copy: bool = True, track: bool = False
) -> np.ndarray | None:
    """recv a numpy array"""
    header = cast(dict[str, Any], socket.recv_json(flags=flags))
    if header.get('done', False):
        return None
    msg = socket.recv(flags=flags, copy=copy, track=track)
    array = np.frombuffer(msg, dtype=header['dtype'])  # type: ignore
    return array.reshape(header['shape'])


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--url", default="tcp://127.0.0.1:5555")
    args = parser.parse_args()

    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)
    s.connect(args.url)
    s.subscribe(b'')

    # md = s.recv_json()
    # msg = s.recv()
    # while msg: 
    #     array = np.frombuffer(msg, dtype=md["dtype"])
    #     array = array.reshape(md["shape"])
    #     print("Ontvangen sensorwaarden:", array)

    while True:
        array = recv_array(s)
        if array is None: #geen array binnen gekomen
            break
        print(array)
    # start = time.perf_counter()
    # print("Receiving arrays...")
    # a = first_array = recv_array(s)
    # assert first_array is not None
    # array_count = 0
    # while a is not None:
    #     array_count += 1
    #     a = recv_array(s)
    # print("   Done.")

    # end = time.perf_counter()

    # elapsed = end - start

    # throughput = float(array_count) / elapsed

    # message_size = first_array.nbytes
    # megabits = float(throughput * message_size * 8) / 1000000

    # print(f"message size: {message_size:.0f} [B]")
    # print(f"array count: {array_count:.0f}")
    # print(f"mean throughput: {throughput:.0f} [msg/s]")
    # print(f"mean throughput: {megabits:.3f} [Mb/s]")


if __name__ == "__main__":
    main()
