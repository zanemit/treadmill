import sys
sys.path.append("./")

from ximea import xiapi #from pypylon import pylon
import skvideo.io
import os
import cv2
import numpy as np
import time

from utils.file_io_utils import * # checks and creates files

class Camera():
    def __init__(self):
        self.frame_count = 0
        self.display_frames = {}

    def start_cameras(self):
        self.get_cameras()  # get the detected cameras
        self.get_camera_writers()   # set up a video grabber for each
        self.setup_cameras()    # set up camera parameters (triggering... )

    def get_cameras(self): # get a single ximea camera
        self.xiCam = xiapi.Camera() # creates instance of the connected camera 
        if not self.xiCam:
            raise ValueError('Could not find a Ximea camera')
        
    def get_camera_writers(self): # open FFMPEG camera writers if we are saving to video
        if self.save_to_video:
            w, h = self.camera_config["acquisition"]["frame_width"], self.camera_config["acquisition"]["frame_height"]
            indict = self.camera_config["inputdict"].copy()
            indict['s'] = '{}x{}'.format(w,h)
            self.xiCamWriter = skvideo.io.FFmpegWriter(self.video_files_names[0], outputdict = self.camera_config["outputdict"], inputdict = indict)
            print("Writing to: {}".format(self.video_files_names[0]))       
         else:
            self.xiCamWriter = None 
            

    def setup_cameras(self):
          # set up cameras
          self.xiCam.open_device()
          print("Using device ", self.xiCam.get_device_name()) #xiGetDeviceInfoString, alternatively get.device_model_id()
          
          
          # set up exposure and frame size
          self.xiCam.set_exposure(int(self.camera_config["acquisition"]["exposure"]))
          self.xiCam.set_width(int(self.camera_config["acquisition"]["frame_width"]))
          self.xiCam.set_height(int(self.camera_config["acquisition"]["frame_heigth"]))
          self.xiCam.set_gain(int(self.camera_config["acquisition"]["gain"]))
          self.xiCam.set_offsetY(int(self.camera_config["acquisition"]["frame_offset_y"]))
          self.xiCam.set_offsetX(int(self.camera_config["acquisition"]["frame_offset_x"]))
          
          
          # trigger mode setup
          if self.camera_config["trigger_mode"]:
              self.xiCam.set_trigger_selector('XI_TRG_SEL_FRAME_START')
              self.xiCam.set_gpi_selector('XI_GPI_PORT1')
              self.xiCam.set_gpi_mode('XI_GPI_TRIGGER')
              self.xiCam.set_trg_source('XI_TRG_EDGE_RISING')
              self.xiCam.set_buffers_queue_size(10)
              self.xiCam.set_acq_transport_buffer_commit(10) # maybe? number of buffers allocated for grabbing    
              
          else:
              self.xiCam.set_gpi_mode('XI_GPI_OFF')
              
          
          # start grabbing
          self.xiCam.start_acquisition()
             
       
    def print_current_fps(self, start):
        now = time.time()
        elapsed = now - start
        start = now

        # Given that we did 100 frames in elapsedtime, what was the framerate
        time_per_frame = (elapsed / 100) * 1000
        fps = round(1000  / time_per_frame, 2) 
        
        print("Total frames: {}, current fps: {}, desired fps {}.".format(
                    self.frame_count, fps, self.acquisition_framerate))
        return start
    
    def grab_frames(self):
        try:
            xiGrab = xiapi.Image()
            xiCam.get_image(TimeOut = self.camera_config["timeout"], xiGrab)
            if self.save_to_video:
                self.xiCamWriter.writeFrame(xiGrab)
        except:
            raise ValueError("xiCam grab failed")
            break

        return [xiGrab]


    def stream_videos(self, max_frames=None):        
        # ? Keep looping to acquire frames
        while True:
            try:
                if self.frame_count % 100 == 0:  # Print the FPS in the last 100 frames
                    if self.frame_count == 0: start = time.time()
                    else: start = self.print_current_fps(start)

                # ! Loop over each camera and get frames
                xiGrab = self.grab_frames()

                # Read the state of the arduino pins and save to file
                sensor_states = self.read_arduino_write_to_file(xiCam.get_timestamp) # use with the regular comms.py

                # Update frame count
                self.frame_count += 1

                # Stop if reached max frames
                if max_frames is not None:
                        if self.frame_count >= max_frames: break

                # stop if enough time has elapsed
                if self.experiment_duration is not None:
                    if time.time() - self.exp_start_time/1000 > self.experiment_duration: 
                        print("Terminating acquisition - reached max time")
                        raise KeyboardInterrupt("terminating") # need to raise an error here to be cached in main

        # Close camera
        xiCam.close_device()

    def close_ffmpeg_writers(self):
        if self.save_to_video: 
            xiCamWriter.close()
    
if __name__ == "__main__":
    cam = Camera()
