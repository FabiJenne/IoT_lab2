from __future__ import annotations

import time
from argparse import ArgumentParser
from typing import Any, cast

import numpy as np

import zmq

import serial
import sys
import csv
import statistics as stat

from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QDateTime, QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QApplication
from lab2_ui import Ui_Form

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


parser = ArgumentParser()
parser.add_argument("--url", default="tcp://127.0.0.1:5555")
args = parser.parse_args()

ctx = zmq.Context()
s = ctx.socket(zmq.SUB)
s.connect(args.url)


def recv_array(
    socket: zmq.Socket, flags: int = 0, copy: bool = True, track: bool = False
) -> tuple[str, np.ndarray] | None:
    """recv a numpy array"""
    topic = socket.recv_string(flags=flags) 
    header = cast(dict[str, Any], socket.recv_json(flags=flags))
    if header.get('done', False):
        return None
    msg = socket.recv(flags=flags, copy=copy, track=track)
    array = np.frombuffer(msg, dtype=header['dtype'])  # type: ignore
    return topic, array.reshape(header['shape'])


class SensorData():

    def __init__(self):
        self._x = []
        self._y = []
        self._z = []
        self._gx = []
        self._gy = []
        self._gz = []
        self.mean_x = 0
        self.mean_y = 0
        self.mean_z = 0
        self.all_mean = 0
        self.std_x = 0
        self.std_y = 0
        self.std_z = 0
        self.all_std = 0
        self._timestamps = []
        self._timestamps2 = []
        self._start_time = datetime.now

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def z(self):
        return self._z

    @property
    def gx(self):
        return self._gx

    @property
    def gy(self):
        return self._gy

    @property
    def gz(self):
        return self._gz

    @property
    def timestamps(self):
        return self._timestamps
    
    @property
    def timestamps2(self):
        return self._timestamps2

    @property
    def start_time(self):
        return self.start_time

    @start_time.setter
    def start_time(self, value):
        self._start_time = value

    def update(self, result, accel, gyro):
        topic, array = result
        if accel and topic == "accel":
            self._x.append(float(array[0]))
            self._y.append(float(array[1]))
            self._z.append(float(array[2]))
            self._timestamps.append((datetime.now() -
                                     self._start_time).total_seconds())
        if gyro and topic == "gyro":
            self._gx.append(float(array[0]))
            self._gy.append(float(array[1]))
            self._gz.append(float(array[2]))
            self._timestamps2.append((datetime.now() -
                                     self._start_time).total_seconds())
            print(self.gx, self.timestamps2)
        # if (gyro and topic == "gyro") or (accel and topic == "accel"):
        self.calc_mean()
        self.calc_std()

    def calc_mean(self):
        if self.x and self.y and self.z:
            self.mean_x = sum(self.x) / len(self.x)
            self.mean_y = sum(self.y) / len(self.y)
            self.mean_z = sum(self.z) / len(self.z)
            self.all_mean = {self.mean_x, self.mean_y, self.mean_z}

    def calc_std(self):
        if len(self.x) and len(self.y) and len(self.z) > 2:
            self.std_x = stat.stdev(self._x)
            self.std_y = stat.stdev(self._y)
            self.std_z = stat.stdev(self._z)
            self.all_std = {self.std_x, self.std_y, self.std_z}


class Lab2(QMainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self)
        self.last_pause_index = 0
        self.ui = Ui_Form()
        self.data = SensorData()
        self.ui.setupUi(self)
        self.mybuttonfunction = self.on_off
        self.ui.pushButton.clicked.connect(self.mybuttonfunction)
        self.ui.pushButton_2.clicked.connect(self.to_file)
        self.setWindowTitle("arduino_sensors")
        self.status = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.plot_data)
        self.ui.MplWidget.canvas.axes.set_ylim(0, 2)  # set lim y-as at 0-10
        self.ui.MplWidget_2.canvas.axes.set_ylim(0, 2)  # set lim y-as at 0-10
        self.ui.checkBox.clicked.connect(self.accel_sub)
        self.ui.checkBox_2.clicked.connect(self.gyro_sub)
        s.subscribe(b'accel')
        s.subscribe(b'gyro')

    def accel_sub(self):
        if self.ui.checkBox.isChecked():
            s.subscribe(b'accel')
        else:
            s.unsubscribe(b'accel')

    def gyro_sub(self):
        if self.ui.checkBox_2.isChecked():
            s.subscribe(b'gyro')
        else:
            s.unsubscribe(b'gyro')

    def plot_data(self):
        result = recv_array(s)
        self.data.update(result, self.ui.checkBox.isChecked(),
                         self.ui.checkBox_2.isChecked())
        if not self.status:
            return
        start = self.last_pause_index
        x = self.data.x[start:]
        y = self.data.y[start:]
        z = self.data.z[start:]
        gx = self.data.gx[start:]
        gy = self.data.gy[start:]
        gz = self.data.gz[start:]
        timestamps = self.data.timestamps[start:]
        timestamps2 = self.data.timestamps2[start:]

        spinBox = self.ui.spinBox.value()
        if spinBox and spinBox < timestamps[-1] - timestamps[0]:
            self.on_off()

        x = x[-20:]
        y = y[-20:]
        z = z[-20:]
        gx = gx[-20:]
        gy = gy[-20:]
        gz = gz[-20:]
        timestamps = timestamps[-20:]
        timestamps2 = timestamps2[-20:]

        print(x, y, z, gx, gy, gz, timestamps)
        self.ui.MplWidget.canvas.axes.clear()
        self.ui.MplWidget.canvas.axes.plot(timestamps, x, 'r', label='x', linewidth=0.5)
        self.ui.MplWidget.canvas.axes.plot(timestamps, y, 'g', label='y', linewidth=0.5)
        self.ui.MplWidget.canvas.axes.plot(timestamps, z, 'b', label='z', linewidth=0.5)
        self.ui.MplWidget.canvas.draw()
        self.ui.MplWidget_2.canvas.axes.clear()
        self.ui.MplWidget_2.canvas.axes.plot(timestamps2, gx, 'c', label='gx', linewidth=0.5)
        self.ui.MplWidget_2.canvas.axes.plot(timestamps2, gy, 'm', label='gy', linewidth=0.5)
        self.ui.MplWidget_2.canvas.axes.plot(timestamps2, gz, 'y', label='gz', linewidth=0.5)
        self.ui.MplWidget_2.canvas.draw()

    def on_off(self):
        if self.status:
            self.timer.stop()
            self.status = 0
            self.last_pause_index = len(self.data.timestamps)
            self.ui.pushButton.setText("Start")
            self.ui.pushButton.setStyleSheet("")
        else:
            self.data.start_time = datetime.now()
            self.timer.start(self.ui.spinBox_2.value())
            self.plot_data()
            self.status = 1
            self.ui.pushButton.setText("Stop")
            self.ui.pushButton.setStyleSheet("background-color : red;" +
                                             "color : white; border: none;" +
                                             "border-radius: 5px;")

    def to_file(self):
        all_data = zip(self.data.timestamps, self.data.x, self.data.y, self.data.z, self.data.gx, self.data.gy, self.data.gz)
        with open("data.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'accel-X', 'accel-Y', 'accel-Z', 'gyro-X', 'gyro-Y', 'gyro-Z'])
            for row in all_data:
                writer.writerow(row)


def main() -> None:
    app = QApplication([])
    form = Lab2()
    form.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
