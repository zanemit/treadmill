import sys
sys.path.append("./")

from pypylon import pylon
import skvideo.io
import os
import cv2
import numpy as np
import time

from utils.file_io_utils import * # checks and creates files

class Camera():
    def __init__(self):
        self.frame_count = 0
        self.cam_writers = {}
        self.grabs = {}
        self.display_frames = {}

    def start_cameras(self):
        self.get_cameras()  # get the detected cameras
        self.get_camera_writers()   # set up a video grabber for each
        self.setup_cameras()    # set up camera parameters (triggering... )

    def get_cameras(self): # get a single ximea camera
        self.tlFactory = pylon.TlFactory.GetInstance()
        self.devices = self.tlFactory.EnumerateDevices()
        if not self.devices: 
            raise ValueError("Could not find any camera")
        else:
            self.cameras = pylon.InstantCameraArray(self.camera_config["n_cameras"])

    def get_camera_writers(self): # open FFMPEG camera writers if we are saving to video
        if self.save_to_video:
            w, h = self.camera_config["acquisition"]["frame_width"], self.camera_config["acquisition"]["frame_height"]
            indict = self.camera_config["inputdict"].copy()
            indict['-s'] = '{}x{}'.format(w,h)
            self.cam0Writer = skvideo.io.FFmpegWriter(self.video_files_names[0], outputdict = self.camera_config["outputdict"], inputdict = indict)
            print("Writing to: {}".format(self.video_files_names[0]))
            self.cam1Writer = skvideo.io.FFmpegWriter(self.video_files_names[1], outputdict = self.camera_config["outputdict"], inputdict = indict)
            print("Writing to: {}".format(self.video_files_names[1]))
         else:
            self.cam0Writer = None 
            self.cam1Writer = None

    def setup_cameras(self):
        #set up cameras
        self.cam0.Attach(self.tlFactory.CreateDevice(self.devices[0]))
        print("Using camera: ", self.cam0.GetDeviceInfo().GetModelName())
        self.cam0.Open()
        self.cam0.RegisterConfiguration(pylon.ConfigurationEventHandler(), pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_Delete)
        
        self.cam1.Attach(self.tlFactory.CreateDevice(self.devices[1]))
        print("Using camera: ", self.cam1.GetDeviceInfo().GetModelName())
        self.cam1.Open()
        self.cam1.RegisterConfiguration(pylon.ConfigurationEventHandler(), pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_Delete)
          
        # set up exposure and frame size
        self.cam0.set_exposure(int(self.camera_config["acquisition"]["cam0Exposure"]))
        self.cam0.set_width(int(self.camera_config["acquisition"]["cam0Frame_width"]))
        self.cam0.set_height(int(self.camera_config["acquisition"]["cam0Frame_heigth"]))
        self.cam0.set_gain(int(self.camera_config["acquisition"]["cam0Gain"]))
        self.cam0.set_offsetY(int(self.camera_config["acquisition"]["cam0Frame_offset_y"]))
        self.cam0.set_offsetX(int(self.camera_config["acquisition"]["cam0Frame_offset_x"]))
          
        self.cam1.ExposureTime.FromString(self.camera_config["acquisition"]["cam1Exposure"])
        self.cam1.Width.FromString(self.camera_config["acquisition"]["cam1Frame_width"])
        self.cam1.Height.FromString(self.camera_config["acquisition"]["cam1Frame_height"])
        self.cam1.Gain.FromString(self.camera_config["acquisition"]["cam1Gain"])
        self.cam1.OffsetY.FromString(self.camera_config["acquisition"]["cam1Frame_offset_y"])
        self.cam1.OffsetX.FromString(self.camera_config["acquisition"]["cam1Frame_offset_x"])
          
        # trigger mode setup
        for cam in [self.cam0, self.cam1]:
            if self.camera_config["trigger_mode"]:
                cam.TriggerSelector.FromString('FrameStart')
                cam.TriggerMode.FromString('On')
                cam.LineSelector.FromString('Line4')
                cam.LineMode.FromString('Input')
                cam.TriggerSource.FromString('Line4')
                cam.TriggerActivation.FromString('RisingEdge')
                cam.OutputQueueSize = 10
                cam.MaxNumBuffer = 10 # number of buffers allocated for grabbing
              
            else:
                cam.TriggerMode.FromString("Off")
          
            # start grabbing      
            self.cam.Open() # again??
            self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    
       
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
            cam0Grab = self.cam0.RetrieveResult(self.camera_config["timeout"])
            if self.save_to_video:
                self.cam0Writer.writeFrame(cam0Grab.Array)
         except:
            raise ValueError("cam0 grab failed")
            
        try:
            cam1Grab = self.cam1.RetrieveResult(self.camera_config["timeout"])
            if self.save_to_video:
                self.cam1Writer.writeFrame(cam1Grab.Array)
         except:
            raise ValueError("cam1 grab failed")
            
        return [cam0Grab, cam1Grab]


    def stream_videos(self, max_frames=None):        
        # ? Keep looping to acquire frames
        # self.grab.GrabSucceeded is false when a camera doesnt get a frame -> exit the loop
        while True:
            try:
                if self.frame_count % 100 == 0:  # Print the FPS in the last 100 frames
                    if self.frame_count == 0: start = time.time()
                    else: start = self.print_current_fps(start)

                # ! Loop over each camera and get frames
                cam0Grab, cam1Grab = self.grab_frames()

                # Read the state of the arduino pins and save to file
                sensor_states = self.read_arduino_write_to_file(cam0Grab.Timestamp, cam1Grab.TimeStamp) # from comms.py

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

            except pylon.TimeoutException as e:
                print("Pylon timeout Exception")
                raise ValueError("Could not grab frame within timeout")

        # Close camera
        self.cam0.close_device()
        self.cam1.Close()

    def close_ffmpeg_writers(self):
        if self.save_to_video: 
            self.cam0Writer.close()
            self.cam1Writer.close()
    
if __name__ == "__main__":
    cam = Camera()
