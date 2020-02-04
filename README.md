# treadmill
This repository contains code to control a motorised treadmill while acquiring its speed readout and video data from two cameras.

One version of the setup involves a Basler and a Ximea camera, while another version uses two Basler cameras. 

Scripts relevant for both setups: 
* cam_speed_millis_firmata.ino - uploaded onto the Arduino to trigger two cameras and acquire treadmill speed data
* file_io_utils.py - deals with folder creation and output file generation
* main.py - run in tandem with Spike2 protocols to control data acquisition

Scripts for the Basler/Ximea version:
* camera_xi_bs.py - sets up, and acquires frames from, a Basler and a Ximea camera
* comms_xi_bs.py - takes care of communication between Python and Arduino
* treadmill_config_xi_bs.py - sets parameters for video data acquisition and output files

Scripts for the two-Basler version:
* camera_bs2.py - sets up, and acquires frames from, two Basler cameras
* comms.py - takes care of communication between Python and Arduino
* treadmill_config.py - sets parameters for video data acquisition and output files

The setup uses an ArduinoMega2560 pictured below:
![ArduinoMega pinout](arduino_mega_pinout.png)
