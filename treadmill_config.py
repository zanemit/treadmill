"""
This code is for a setup with two Basler cameras and a treadmill controlled by the Spike2 software.
"""

from utils.colors import *

# Define a config class with all the options for data acquisition and post-hoc analysis
class Config:
    """
        ############## EXPERIMENT CONFIG  ####################
    """

    # ! Change these for every recording
    experiment_folder = "D:\\ZM\\200114"   # ? This should be changed for every experiment to avoid overwriting 
    experiment_name = "200114_518_3_0.5V"  # should be something like YYMMDD_MOUSEID, all files for an experiment will start with this name
    experiment_duration = 1*25  # acquisition duration in seconds, alternatively set as None

    # * Check that these options are correct
    com_port = "COM3"  # port of the arduino running Firmata for data acquisition
    acquisition_framerate = 200  # fps of camera triggering -> NEED TO SPECIFY INTERVALS IN ARDUINO for frame triggering
    # this number is just indicative as the true acquisition rate depends on the trigger arduino

    overwrite_files = True # ! ATTENTION: this is useful for debug but could lead to overwriting experimental data
    
    save_to_video = True  # ! decide if you want to save the videos or not

    """
        ############## POST-HOC ANALYSIS  ####################
    """
    analysis_config = { 
        "data_folder": "D:\\Zane\\Plot-videos DLC", # where the data to analyse are stored
        "experiment_name": "test",
        "plot_colors": { "emg1":pink, 
                        "emg2":peach, 
                        "emg3":aqua, 
                        "emg4":purple},

        # * for composite video
        # ? run video_analysis.py
        "start_clip_time_s": None, # ? Create clips start at this point, in SECONDS
        "start_clip_time_frame": 1, # ? Create clips start at this point, in FRAMES
        "clip_n_frames": 100 , # duration of the clip in frames
        "clip_name":"test", 

        "outputdict":{ # for ffmpeg
                    # '-vcodec': 'mpeg4',  #  high fps low res
                    "-vcodec": "libx264",   #   low fps high res
                    '-crf': '0',
                    '-preset': 'slow',  # TODO check this
                    '-pix_fmt': 'yuvj444p',
                    "-framerate": "10", #   output video framerate 
                    # TODO this doesnt work FPS
                },
    }


    """
        ############## CAMERA CONFIG  ####################
    """
    # * These options should not be changed frequently unless  something changes in the experiment set up

    camera_config = {
        "video_format": ".avi",
        "n_cameras": 2,  # initially just the basler
        "timeout": 100,   # frame acquisition timeout

        # ? Trigger mode and acquisition options -> needed for constant framerate
        "trigger_mode": True,  # hardware triggering
        "acquisition": {    
            "cam0Exposure": "1000", 
            "cam0Frame_width": "608",  # must be a multiple of 32 (e.g.288) 
            "cam0Frame_height": "256", # must be a multiple of 32 (e.g.288)
            "cam0Gain": "7.4", #12
            "cam0Frame_offset_y": "64", #612
            "cam0Frame_offset_x": "32", #672
            "cam1Exposure": "1000", 
            "cam1Frame_width": "1312",  # must be a multiple of 32 (e.g.288)
            "cam1Frame_height": "512", # must be a multiple of 32 (e.g.288)
            "cam1Gain": "12", #12
            "cam1Frame_offset_y": "484", #612
            "cam1Frame_offset_x": "672", #672
        },

        # all commands and options  https://gist.github.com/tayvano/6e2d456a9897f55025e25035478a3a50
        # pixel formats https://ffmpeg.org/pipermail/ffmpeg-devel/2007-May/035617.html

        "outputdict":{
            "-c:v": 'libx264',   #   low fps high res
            "-crf": '17',
            "-preset": 'ultrafast',
            "-pix_fmt": 'yuv444p',
            "-r": str(acquisition_framerate),
        },

        "inputdict":{
            "-r": str(acquisition_framerate),
        }
    }

    """
        ############## FIRMATA ARDUINO CONFIG  ####################
    """
    # Arduino (FIRMATA) setup options
    # * Only change these if you change the configuration of the inputs coming onto the firmata arduino
    arduino_config = {
        "sensors_pins": {
                # Specify the pins receiving input from treadmill (or emgs)
                "trdmSpeed": 0,  
        },
        "arduino_csv_headers": ["frame_number", "elapsed", "cam0_timestamp", "cam1_timestamp", "trdmSpeed"],
        "sensors": [ "trdmSpeed"],
    }

    def __init__(self): 
        return # don't need to do anything but we need this func
