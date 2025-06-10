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

    while True:
        array = recv_array(s)
        if array is None: #geen array binnen gekomen
            break
        print(array)


if __name__ == "__main__":
    main()
