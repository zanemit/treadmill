import sys
sys.path.append("./")

from ximea import xiapi #from pypylon import pylon
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
        self.xiCam = xiapi.Camera() # creates instance of the connected camera 
        self.bsCam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice()) # creates instance of the first connected camera
        if not self.xiCam:
            raise ValueError('Could not find a Ximea camera')
        if not self.bsCam:
            raise ValueError('Could not find a Basler camera')
        
        #self.devices = self.tlFactory.EnumerateDevices()
        #if not self.devices: 
        #    raise ValueError("Could not find any camera")
        #else:
        #    self.cameras = pylon.InstantCameraArray(self.camera_config["n_cameras"])  

    def get_camera_writers(self): # open FFMPEG camera writers if we are saving to video
        if self.save_to_video: 
            for i, file_name in enumerate(self.video_files_names):
                w, h = self.camera_config["acquisition"]['frame_width'], self.camera_config["acquisition"]['frame_height']
                indict = self.camera_config['inputdict'].copy()
                indict['-s'] = '{}x{}'.format(w,h)
                self.cam_writers[i] = skvideo.io.FFmpegWriter(file_name, outputdict=self.camera_config["outputdict"], inputdict=indict)

                print("Writing to: {}".format(file_name))
        else:
            self.cam_writers = {str(i):None for i in np.arange(self.camera_config["n_cameras"])}

    def setup_cameras(self):
          # set up cameras
          self.xiCam.open_device()
          print("Using device ", self.xiCam.get_device_name()) #xiGetDeviceInfoString, alternatively get.device_model_id()
          
          self.bsCam.Open()
          print("Using device ", self.bsCam.GetDeviceInfo().GetModelName())
          self.bsCam.RegisterConfiguration(pylon.ConfigurationEventHandler(), 
                                        pylon.RegistrationMode_ReplaceAll, 
                                        pylon.Cleanup_Delete)
          
          # set up exposure and frame size
          self.xiCam.set_exposure(int(self.camera_config["acquisition"]["exposure"]))
          self.xiCam.set_width(int(self.camera_config["acquisition"]["frame_width"]))
          self.xiCam.set_height(int(self.camera_config["acquisition"]["frame_heigth"]))
          self.xiCam.set_gain(int(self.camera_config["acquisition"]["gain"]))
          self.xiCam.set_offsetY(int(self.camera_config["acquisition"]["frame_offset_y"]))
          self.xiCam.set_offsetX(int(self.camera_config["acquisition"]["frame_offset_x"]))
          
          self.bsCam.ExposureTime.FromString(self.camera_config["acquisition"]["exposure"])
          self.bsCam.Width.FromString(self.camera_config["acquisition"]["frame_width"])
          self.bsCam.Height.FromString(self.camera_config["acquisition"]["frame_height"])
          self.bsCam.Gain.FromString(self.camera_config["acquisition"]["gain"])
          self.bsCam.OffsetY.FromString(self.camera_config["acquisition"]["frame_offset_y"])
          self.bsCam.OffsetX.FromString(self.camera_config["acquisition"]["frame_offset_x"])
          
          # trigger mode setup
          if self.camera_config["trigger_mode"]:
              self.xiCam.set_gpi_selector('XI_GPI_PORT1')
              self.xiCam.set_gpi_mode('XI_GPI_TRIGGER')
              self.xiCam.set_trg_source('XI_TRG_EDGE_RISING')
              self.xiCam.set_buffers_queue_size = 10
              # anything analogous to maxnumbuffer??
              
              self.bsCam.TriggerSelector.FromString('FrameStart')
              self.bsCam.TriggerMode.FromString('On')
              self.bsCam.LineSelector.FromString('Line4')
              self.bsCam.LineMode.FromString('Input')
              self.bsCam.TriggerSource.FromString('Line4')
              self.bsCam.TriggerActivation.FromString('RisingEdge')
              self.bsCam.OutputQueueSize = 10
              self.bsCam.MaxNumBuffer = 10
          else:
              self.bsCam.TriggerMode.FromString("Off")
              # anything analogous for ximea??
          
          # start grabbing
          self.xiCam.start_acquisition()
          
          self.bsCam.Open() # again??
          self.bsCam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    
      
       
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
        for i, (writer, cam) in enumerate(zip(self.cam_writers.values(), self.cameras)): 
            try:
                grab = cam.RetrieveResult(self.camera_config["timeout"])
            except:
                raise ValueError("Grab failed")

            if not grab.GrabSucceeded():
                break
            else:
                if self.save_to_video:
                    writer.writeFrame(grab.Array)
                pass

            if self.live_display:
                image_windows[i].SetImage(grab)
                image_windows[i].Show()
        return grab


    def stream_videos(self, max_frames=None):
        # Set up display windows
        if self.live_display:
            image_windows = [pylon.PylonImageWindow() for i in self.cameras]
            self.pylon_windows = image_windows
            for i, window in enumerate(image_windows): window.Create(i)
        
        # ? Keep looping to acquire frames
        # self.grab.GrabSucceeded is false when a camera doesnt get a frame -> exit the loop
        while True:
            try:
                if self.frame_count % 100 == 0:  # Print the FPS in the last 100 frames
                    if self.frame_count == 0: start = time.time()
                    else: start = self.print_current_fps(start)

                # ! Loop over each camera and get frames
                grab = self.grab_frames()

                # Read the state of the arduino pins and save to file
                sensor_states = self.read_arduino_write_to_file(grab.TimeStamp) # from comms.py

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
        for cam in self.cameras: cam.Close()

    def close_pylon_windows(self):
        if self.live_display:
            for window in self.pylon_windows:
                window.Close()

    def close_ffmpeg_writers(self):
        if self.save_to_video: 
            for writer in self.cam_writers.values():
                writer.close()

    # def close
    
if __name__ == "__main__":
    cam = Camera()
