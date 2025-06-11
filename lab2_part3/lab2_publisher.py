"""
lab2_sensor_template
----------------

sensor reading example T.R. Walstra, may 2024
"""

import argparse
import asyncio
import logging
import struct
from bleak import BleakClient, BleakScanner
from argparse import ArgumentParser
import numpy as np
import zmq

import keyboard

BLE_UUID_ACCEL_SENSOR_DATA = "4664E7A1-5A13-BFFF-4636-7D0A4B16496C"
BLE_UUID_GYRO_SENSOR_DATA = "4664E7A1-5A13-BFFF-4636-7D0A4B16496D"
exit_flag = False

logger = logging.getLogger(__name__)

ctx = zmq.Context()
# s = ctx.socket(zmq.XPUB)
s = ctx.socket(zmq.PUB)


def notification_handler_accel(sender, data):
    sensorvalues = struct.unpack("fff", data)
    ##############################publisher
    array = np.array(sensorvalues, dtype=np.float32)
    md = {"shape": array.shape, "dtype": str(array.dtype)}
    
    s.send_string("accel", zmq.SNDMORE)  # topic als eerste frame
    s.send_json(md, zmq.SNDMORE) #send sequence of buffers aka not the last
    s.send(array)
    ##############################publisher

def notification_handler_gyro(sender, data):
    sensorvalues = struct.unpack("fff", data)
    array = np.array(sensorvalues, dtype=np.float32)
    md = {"shape": array.shape, "dtype": str(array.dtype)}
    
    s.send_string("gyro", zmq.SNDMORE)  # topic als eerste frame
    s.send_json(md, zmq.SNDMORE) #send sequence of buffers aka not the last
    s.send(array)


async def main(args: argparse.Namespace):
    global exit_flag

    ##############################publisher
    s.bind(args.url)
    # print("Waiting for subscriber")
    # s.recv()
    # print("Sending arrays...")
    ##############################publisher

    logger.info("starting scan...")

    device = await BleakScanner.find_device_by_name(
          args.name, cb=dict(use_bdaddr=args.macos_use_bdaddr))
    if device is None:
        logger.error("could not find device with name '%s'", args.name)
        return

    print("connecting to device...")
    print("device name:", device.name)
    print("device addr:", device.address)
    print("services: ", args.services)

    async with BleakClient(
        device,
        services=args.services,
    ) as client:
        logger.info("connected")

        await client.start_notify(BLE_UUID_ACCEL_SENSOR_DATA,
                                  notification_handler_accel) #bleak roept not_hand aan waardoor geen arg nodig voor uuid en data-bytes
        await client.start_notify(BLE_UUID_GYRO_SENSOR_DATA,
                                  notification_handler_gyro) #bleak roept not_hand aan waardoor geen arg nodig voor uuid en data-bytes

        while not exit_flag:
            if keyboard.is_pressed('a'):
                exit_flag = True
            await asyncio.sleep(1.0)
            print(".")

        logger.info("disconnecting...")

    await client.stop_notify(BLE_UUID_ACCEL_SENSOR_DATA)
    await client.stop_notify(BLE_UUID_GYRO_SENSOR_DATA)
    s.send_json({"done": True})
    s.close()
    logger.info("disconnected")


if __name__ == "__main__":

#execute this file as: "python lab2_sensor.py --name <arduino_local_name>

    parser = argparse.ArgumentParser()

    device_group = parser.add_mutually_exclusive_group(required=True)

    device_group.add_argument(
        "--name",
        metavar="<name>",
        help="the name of the bluetooth device to connect to",
    )
    device_group.add_argument(
        "--address",
        metavar="<address>",
        help="the address of the bluetooth device to connect to",
    )

    parser.add_argument(
        "--macos-use-bdaddr",
        action="store_true",
        help="when true use Bluetooth address instead of UUID on macOS",
    )

    parser.add_argument(
        "--services",
        nargs="+",
        metavar="<uuid>",
        help="if provided, only enumerate matching service(s)",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="sets the log level to debug",
    )

    ##############################publisher
    parser.add_argument("--url", default="tcp://127.0.0.1:5555")
    ##############################publisher

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    asyncio.run(main(args))
