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

BLE_UUID_ACCEL_SENSOR_DATA = "4664E7A1-5A13-BFFF-4636-7D0A4B16496C"
exit_flag = False

logger = logging.getLogger(__name__)


def notification_handler(sender,data):
    #convert the data into 3 floats
    sensorvalues = struct.unpack("fff", data)
    print("data:",sensorvalues)

async def main(args: argparse.Namespace):
    global exit_flag

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


#your code here
#Get the client services and use the read_gatt_char from the client. Check if
#the value is the UUID above and start a notification handler using the client 
#start_notify function of Bleak. The async await takes care that this function
# is executed on each notification of data from the arduino
#Read the data and print it. 
#

        # await client.read_gatt_char(BLE_UUID_ACCEL_SENSOR_DATA) #eenmalig uitlezen GATT characteristic, geeft bytes terug
        await client.start_notify(BLE_UUID_ACCEL_SENSOR_DATA,
                                  notification_handler)
        

        while not exit_flag:
            await asyncio.sleep(1.0)
            print(".")

        logger.info("disconnecting...")

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

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    asyncio.run(main(args))
