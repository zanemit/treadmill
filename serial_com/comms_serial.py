"""
        ONE BASLER CAMERA + TREADMILL SPEED
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


    def connect_serial(self):
        ser = serial.Serial(self.com_port, timeout=1)
        ser.baudrate  = 115200
        print(ser.name, "is open: ", ser.is_open)
        if ser.is_open: self.serial = ser
        else: 
            self.serial is None
            warnings.warn("Could not connet to serial on port: {}".format(self.com_port))


    def read_serial(self):
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

        ser_bytes = self.serial.readline().decode('utf-8')
        if ('+' in ser_bytes) and ('!' in ser_bytes): #received line is correct
            cleaned = ser_bytes.strip('!+\r\n') #remove extra characters
            cleaned = cleaned.split(";")  #splits characters

            # convert to floats, but only return i we have all data
            try:
                numbers = [float(c) for c in cleaned]
                return numbers
            except:
                print(ser_bytes)
                raise
        else:
            pass


    def read_arduino_write_to_file(self, camera_timestamp):
        # read the state of the arduino inputs and append it to the .csv file with the experimental data   
        arduino_inputs = self.read_serial()     
        if arduino_inputs: #if received an input list e.g. [1.0, 365] as should be the case
            trdmSpeed = arduino_inputs[1]
        else:
            trdmSpeed = '-'

        states = {'trdmSpeed': trdmSpeed} #make dict
        states["frame_number"] = self.frame_count
        now = time.time() * 1000
        states["elapsed"] = now - self.exp_start_time
        states["camera_timestamp"] = camera_timestamp

        append_csv_file(self.arduino_inputs_file, states, self.arduino_config["arduino_csv_headers"])

        return states
