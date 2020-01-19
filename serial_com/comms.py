"""
This code is for a setup with two independent Basler cameras and a treadmill controlled by the Spike2 software.
"""

# after adding EMGs in the arduino, change the 'expected' number of serial inputs below (currently 1, will be 5)

import serial
import warnings
import numpy as np
from pyfirmata2 import ArduinoMega as Arduino
from pyfirmata2 import util, INPUT, OUTPUT
import sys
import time

from utils.file_io_utils import * # checks/creates files


class SerialComm:
	def __init__(self):
		pass

	def get_available_ports(self):
		if sys.platform.startswith('win'):
			ports = ['COM%s' % (i + 1) for i in range(256)]
		elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
			ports = glob.glob('/dev/tty[A-Za-z]*')
		elif sys.platform.startswith('darwin'):
			ports = glob.glob('/dev/tty.*')
		else:
			raise EnvironmentError('Unsupported platform')

		result = []
		for port in ports:
			try:
				s = serial.Serial(port)
				s.close()
				result.append(port)
			except (OSError, serial.SerialException):
				pass
			
		print(result)
		self.available_ports = result

	def connect_firmata(self):
		print("Connecting to arduino... ")
		self.arduino = Arduino(self.com_port)
		print("			... connected")

		
	def setup_pins(self): # given an arduino connected to firmata, create variables to reference the different pins
  		# arduino.config is originally from forceplate_config.py, here treadmill_config.py
		self.arduino_inputs = {k:self.arduino.analog[p] for k,p in self.arduino_config["sensors_pins"].items()}
		for pin in self.arduino_inputs.values(): pin.enable_reporting()

		# start board iteration
		it = util.Iterator(self.arduino)
		it.start()

	def read_arduino_inputs(self):
		return {k: pin.read() for k,pin in self.arduino_inputs.items()}

	def read_arduino_write_to_file(self, cam1_timestamp, cam2_timestamp):
		# read the state of the arduino inputs and append it to the .csv file with the experimental data
		states = self.read_arduino_inputs()
		sensor_states = states.copy() #keep a clean copy

		states["frame_number"] = self.frame_count
		now = time.time() * 1000
		states["elapsed"] = now - self.exp_start_time
		states["cam0_timestamp"] = cam0_timestamp
		states["cam1_timestamp"] = cam1_timestamp

		append_csv_file(self.arduino_inputs_file, states, self.arduino_config["arduino_csv_headers"])

		return sensor_states
