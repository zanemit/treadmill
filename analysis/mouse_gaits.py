import sys
sys.path.append("./")

import os
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt
from analysis.analysis_config import Config
from analysis.interactive import Interactive
import cv2

class GaitAnalyser(Config, Interactive):
        def __init__(self, voltage):
            plt.ioff()  # make sure plt is not in interactive mode
                
            Config.__init__(self)
            Interactive.__init__(self)
            self.voltage = voltage
            self.arduino_folder = os.path.join(self.analysis_config["data_folder"], self.analysis_config["experiment_date"]+ "_" + self.analysis_config["experiment_type"])
            self.dlc_folder = os.path.join(self.analysis_config["data_folder"], self.analysis_config["experiment_date"] + "_DLC")
            self.dlc_file_ext = 'DeepCut_resnet50_DLC' + self.analysis_config["dlc_project_date"] + 'shuffle1_' + self.analysis_config["dlc_iters"]
        
        # extracts x y coordinates of the tape roll
        def extract_h5(self, cam = 'cam0'):
            os.chdir(os.path.join(self.dlc_folder, cam))
            filename = self.analysis_config['experimenter'] + '_' + self.analysis_config["experiment_date"] + '_' + \
                        self.analysis_config["experiment_type"] + '_' + self.analysis_config["mouse_id"] + '_' + \
                        str(self.voltage) + 'V_' + cam + self.dlc_file_ext + '.h5' # dlc file
            data = pd.read_hdf(filename)
            lHx= np.asarray(data[self.dlc_file_ext]['left_hindpaw']['x']); lHy = np.asarray(data[self.dlc_file_ext]['left_hindpaw']['y']);
            rHx = np.asarray(data[self.dlc_file_ext]['right_hindpaw']['x']); rHy = np.asarray(data[self.dlc_file_ext]['right_hindpaw']['y'])
            lFx = np.asarray(data[self.dlc_file_ext]['left_forepaw']['x']); lFy = np.asarray(data[self.dlc_file_ext]['left_forepaw']['y'])
            rFx = np.asarray(data[self.dlc_file_ext]['right_forepaw']['x']); rFy= np.asarray(data[self.dlc_file_ext]['right_forepaw']['y'])
            rEx = np.asarray(data[self.dlc_file_ext]['right_ear']['x']); rEy = np.asarray(data[self.dlc_file_ext]['right_ear']['y'])
            lEx = np.asarray(data[self.dlc_file_ext]['left_ear']['x']); lEy = np.asarray(data[self.dlc_file_ext]['left_ear']['y'])
            Tx = np.asarray(data[self.dlc_file_ext]['tail_base']['x']); Ty = np.asarray(data[self.dlc_file_ext]['tail_base']['y'])
            return (lHx,lHy,rHx,rHy,lFx,lFy,rFx,rFy,rEx,rEy,lEx,lEy,Tx,Ty)

        # extracts speed data and timestamp
        def extract_csv(self):
            os.chdir(self.arduino_folder)
            filename = self.analysis_config['experimenter'] + '_' + self.analysis_config["experiment_date"] + '_' + \
                        self.analysis_config['experiment_type'] + '_' + self.analysis_config['mouse_id'] + '_' + str(self.voltage) + 'V_analoginputs.csv' # trdm speed output file
            data = pd.read_csv(filename)
            speed_data = np.asarray(data['trdmSpeed'])*100 # returns treadmill speed in cm/s
            timestamp_cam0 = np.asarray(data['xiCam_timestamp']) # returns timestamp in nanoseconds
            timestamp_cam1 = np.asarray(data['bsCam_timestamp']) # returns timestamp in nanoseconds
            return (speed_data, timestamp_cam0, timestamp_cam1)
        
        def initialise_data(self):
            self.lHx0,self.lHy0,self.rHx0,self.rHy0,self.lFx0,self.lFy0,self.rFx0,self.rFy0,self.rEx0,self.rEy0,self.lEx0,self.lEy0,self.Tx0,self.Ty0 = self.extract_h5(cam = 'cam0')
            self.lHx1,self.lHy1,self.rHx1,self.rHy1,self.lFx1,self.lFy1,self.rFx1,self.rFy1,self.rEx1,self.rEy1,self.lEx1,self.lEy1,self.Tx1,self.Ty1 = self.extract_h5(cam = 'cam1')
            self.trdm_speed, self.timestamp_cam0, self.timestamp_cam1 = self.extract_csv()
            self.timeax_processed = np.linspace(0,(self.timestamp_cam1[-1]-self.timestamp_cam1[0])/(10**9),num=len(self.timestamp_cam1)-1) # time in seconds (len = len-1)
            self.timeax_raw = np.linspace(0,(self.timestamp_cam1[-1]-self.timestamp_cam1[0])/(10**9),num=len(self.timestamp_cam1)) # time in  seconds (len = len)

        def delta(self, inputlist):
                deltalist = []
                for i in range(len(inputlist)-1):
                        delta = inputlist[i+1] - inputlist[i]
                        deltalist.append(delta)
                return np.asarray(deltalist)
        
        def find_analysis_window(self, inputlist, binary = False, filter = True, threshold = 100, filter_order = 2, filter_freq = 5):
            """
            ############## FILTER?  ####################
            """
            if filter:
                filtered_inputlist = self.butter_filter(inputlist, filter_order = filter_order, filter_freq = filter_freq)
            else:
                filtered_inputlist = inputlist

            """
            ############## GET CONSISTENT WINDOWS  ####################
            """
            increasing_list = [] # contains indices for which the next 'threshold' number of elements are consistently increasing
            decreasing_list = [] # contains indices for which the next 'threshold' number of elements are consistently decreasing

            if not binary:
                for i in range(len(filtered_inputlist)-threshold):
                    increasing_truthlist = [] # True when all 'threshold' number of elements are pairwise increasing
                    decreasing_truthlist = [] # True when all 'threshold' number of elements are pairwise decreasing
                    for k in range(i,i+threshold-1):
                        increasing_truthlist.append(filtered_inputlist[k+1] > filtered_inputlist[k])
                        decreasing_truthlist.append(filtered_inputlist[k+1] < filtered_inputlist[k])
                    if np.all(increasing_truthlist):
                        increasing_list.append(i)
                    if np.all(decreasing_truthlist):
                        decreasing_list.append(i)

            else:
                for i in range(len(filtered_inputlist)):
                    if filtered_inputlist[i] == 0:
                        decreasing_list.append(i)
            
            """
            ############## GET START/END POINTS ####################
            """
            upramp_end_ids = []
            if not binary:
                for z in range(len(increasing_list)-1):
                    if (increasing_list[z+1]-increasing_list[z] != 1):
                        upramp_end_ids.append(increasing_list[z] + threshold)
                upramp_end_ids.append(increasing_list[-1] + threshold) 
            
            else:
                for z in range(len(decreasing_list)-1):
                    if (decreasing_list[z+1]-decreasing_list[z] != 1):
                        upramp_end_ids.append(decreasing_list[z])
                upramp_end_ids.append(decreasing_list[-1])
                             
            downramp_start_ids = [decreasing_list[0]]
            for z in range(1,len(decreasing_list)):
                if (decreasing_list[z]-decreasing_list[z-1] !=1):
                    downramp_start_ids.append(decreasing_list[z])
                            
            return (upramp_end_ids, downramp_start_ids)

        def sign_func(self, inputlist, min_step_len = 10):
            count_neg = 0
            count_pos = 0
            for i in range(len(inputlist)):
                if inputlist[i]<= 0:
                    inputlist[i] = -30
                    if (count_neg > 0) & (count_neg < min_step_len):
                        inputlist[(i-count_neg):i] = -30
                    count_neg = 0
                    count_pos += 1
                else:
                    inputlist[i] = 0
                    if (count_pos > 0) & (count_pos < min_step_len):
                        inputlist[(i-count_pos):i] = 0
                    count_pos = 0
                    count_neg += 1
            return(inputlist)
        
        def butter_filter(self, inputlist, filter_order = 2, filter_freq = 5):
            b,a = butter(filter_order, filter_freq, btype = 'low', fs = 200)
            outputlist = filtfilt(b,a, inputlist)
            return outputlist

        def get_limb_baseline(self, inputlist, fraction = 0.9):
            inputlist_sorted = np.sort(inputlist)[::-1] # descending order
            baseline = np.mean(inputlist_sorted[0:int(len(inputlist_sorted)*fraction)])
            return baseline

        def plot_trajectories(self, videoplot = False, staticplot = True, interactive = False):
            # filter the limb ycoords
            lHy1 = self.butter_filter(self.lHy1, filter_order = 2, filter_freq = 20)
            rHy0 = self.butter_filter(self.rHy0, filter_order = 2, filter_freq = 20)
            lFy1 = self.butter_filter(self.lFy1, filter_order = 2, filter_freq = 20)
            rFy0 = self.butter_filter(self.rFy0, filter_order = 2, filter_freq = 20)
                
            # treadmill on/off times
            trdm_on, trdm_off = self.find_analysis_window(self.trdm_speed, threshold = 100, filter_order = 2, filter_freq = 5)
            self.trdm_on = trdm_on[0]; self.trdm_off = trdm_off[0]
            
            # get baseline and the sign func
            lHy1_bsl = self.get_limb_baseline(lHy1, fraction = 0.9); self.lHy1_sign = self.sign_func(lHy1-lHy1_bsl, min_step_len = 7)
            rHy0_bsl = self.get_limb_baseline(rHy0, fraction = 0.9); self.rHy0_sign = self.sign_func(rHy0-rHy0_bsl, min_step_len = 7)
            lFy1_bsl = self.get_limb_baseline(lFy1, fraction = 0.7); self.lFy1_sign = self.sign_func(lFy1-lFy1_bsl, min_step_len = 7)
            rFy0_bsl = self.get_limb_baseline(rFy0, fraction = 0.6); self.rFy0_sign = self.sign_func(rFy0-rFy0_bsl, min_step_len = 7)

            # get gait cycle boundaries
            self.lHy1_swing, self.lHy1_stance = self.get_gait_cycle_boundaries(self.lHy1_sign)
            self.rHy0_swing, self.rHy0_stance = self.get_gait_cycle_boundaries(self.rHy0_sign)
            self.lFy1_swing, self.lFy1_stance = self.get_gait_cycle_boundaries(self.lFy1_sign)
            self.rFy0_swing, self.rFy0_stance = self.get_gait_cycle_boundaries(self.rFy0_sign)

            # videoplotting
            if videoplot:
                self.videoplot(inputlist1 = self.lHy1_sign, timeax1 = self.timeax_raw, inputlist2 = lHy1-lHy1_bsl, timeax2 = self.timeax_raw, ylabel = 'X coordinate')
    
            # plotting
            if staticplot:
                f,ax = plt.subplots(4,1)
                # plot trdm on/off times
                ax[0].axvline(self.trdm_on, color = self.colors['grey']); ax[0].axvline(self.trdm_off, color = self.colors['grey'])
                ax[1].axvline(self.trdm_on, color = self.colors['grey']); ax[1].axvline(self.trdm_off, color = self.colors['grey'])
                ax[2].axvline(self.trdm_on, color = self.colors['grey']); ax[2].axvline(self.trdm_off, color = self.colors['grey'])
                ax[3].axvline(self.trdm_on, color = self.colors['grey']); ax[3].axvline(self.trdm_off, color = self.colors['grey'])
                
                # plot raw data
                ax[0].plot(self.lHy1-lHy1_bsl, color = self.colors['aqua'])
                ax[1].plot(self.rHy0-rHy0_bsl, color = self.colors['purple'])
                ax[2].plot(self.lFy1-lFy1_bsl, color = self.colors['peach'])
                ax[3].plot(self.rFy0-rFy0_bsl, color = self.colors['green'])

                # plot filter data
                ax[0].plot(lHy1-lHy1_bsl, color = 'grey')
                ax[1].plot(rHy0-rHy0_bsl, color = 'grey')
                ax[2].plot(lFy1-lFy1_bsl, color = 'grey')
                ax[3].plot(rFy0-rFy0_bsl, color = 'grey')

                # plot sign func
                ax[0].plot(self.lHy1_sign, color = 'black')
                ax[1].plot(self.rHy0_sign, color = 'black')
                ax[2].plot(self.lFy1_sign, color = 'black')
                ax[3].plot(self.rFy0_sign, color = 'black')

                ax[0].scatter(self.lHy1_stance, self.lHy1_sign[self.lHy1_stance], color = 'red')
                ax[0].scatter(self.lHy1_swing, self.lHy1_sign[self.lHy1_swing], color = 'orange')
                plt.show()
            
            if interactive:
                from matplotlib.widgets import Slider

                # variables to be edited
                epsilon = 5
                pind = None
                ylist = self.lHy1
                ylist_bsl = lHy1_bsl
                ylist_sign = self.lHy1_sign
                ylist_stance = self.lHy1_stance
                ylist_swing = self.lHy1_swing

                fig,ax = plt.subplots(1,1)
                x = range(len(ylist))
                ax.plot(x, ylist-ylist_bsl, color = self.colors['aqua'])
                ax.plot(x, ylist_sign, color = 'black')              
                st, = ax.plot (ylist_stance, ylist_sign[ylist_stance], color='red', linestyle='none', marker='o', markersize=8)
                sw, = ax.plot (ylist_swing, ylist_sign[ylist_swing], color='orange', linestyle='none', marker='o', markersize=8)

                stSliders = []
                for i in range(len(ylist_stance)):
                    sliderax = plt.axes([0,0,0,0])
                    s = Slider(sliderax, 'p{0}'.format(i), -35, 5, valinit=ylist_sign[ylist_stance[i]])
                    stSliders.append(s)
                for i in range(len(ylist_stance)):
                    #stSliders[i].on_changed(self.update(xmarkers = ylist_stance, ymarkers = ylist_sign[ylist_stance], sliders = stSliders, axes = st))
                    stSliders[i].on_changed(self.update)


                fig.canvas.mpl_connect('button_press_event', self.button_press_callback(event, xmarkers = ylist_stance, ymarkers = ylist_sign[ylist_stance], axes = ax, epsilon = epsilon))
                fig.canvas.mpl_connect('button_release_event', self.button_release_callback)
                #fig.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback(xfunc = x, yfunc = ylist_sign, xmarkers = ylist_stance, ymarkers = ylist_sign[ylist_stance], sliders = stSliders))
                fig.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)

                plt.show()

        def videoplot(self, inputlist1, timeax1, inputlist2, timeax2, ylabel = 'Mouse velocity (cm/s)'):
            fig, ax = plt.subplots(1,1)
            plt.ion()
            plt.show()
            filepath = os.path.join(self.arduino_folder,self.analysis_config['experimenter'] + '_' + self.analysis_config["experiment_date"] + '_' + \
                    self.analysis_config['experiment_type'] + '_' + self.analysis_config['mouse_id'] + '_' + str(self.voltage) + 'V_cam1.avi')
            cap = cv2.VideoCapture(filepath)
            while(cap.isOpened()):
                for i in range(len(inputlist2)):
                    ret, frame = cap.read()
                    if ret == True:
                        cv2.imshow('frame', frame)
                        ax.clear()
                        ax.set_xlabel('Time (s)'); ax.set_ylabel(ylabel)
                        ax.plot(timeax1,inputlist1, color = self.colors['peach'])
                        ax.plot(timeax2,inputlist2, color = self.colors['grey'])
                        ax.scatter(timeax1[i], inputlist1[i], color = 'black', s=30, zorder=3)
                        fig.canvas.draw()
                        if cv2.waitKey(15) & 0xFF == ord('q'): 
                            cap.release()
                            cv2.destroyAllWindows()
                    else:
                        break
            cap.release()
            cv2.destroyAllWindows()

        def track_mouse_speed(self, videoplot = False, staticplot = False):
            lEx1 = -self.butter_filter(self.lEx1, filter_order = 2, filter_freq = 5)
            trdm_speed_filt = self.butter_filter(self.trdm_speed, filter_order = 2, filter_freq = 5)

            lEx1_delta = self.delta(lEx1)*18/1013 # calculates cm moved in x per frame
            timestamp_delta = self.delta(self.timestamp_cam1)/(10**9) # calculates seconds per frame
            lEx1_speed = lEx1_delta / timestamp_delta

            mouse_speed = trdm_speed_filt [:-1]+ lEx1_speed # mouse speed is calculated as movement relative to trdm speed - it is also ~trdm speed if mouse is pushed against the back wall
            self.mouse_speed = self.butter_filter(mouse_speed, filter_order = 2, filter_freq = 5)

            # find where mouse is pushed against the back wall (where its ear xcoord is above a threshold: 900 looks appropriate in this case)
            self.ids_back_wall = np.where(self.trdm_speed[self.lEx1 > 900])[0]

            if videoplot:
                self.videoplot(inputlist1 = self.mouse_speed, timeax1 = self.timeax_processed, inputlist2 = trdm_speed_filt, timeax2 = self.timeax_raw, ylabel = 'Mouse velocity (cm/s)')

            if staticplot:
                fig, ax = plt.subplots(1,1)
                ax.plot(self.timeax_raw,trdm_speed_filt, color = 'black', label = 'Treadmill speed')
                ax.plot(self.timeax_processed,self.mouse_speed, color = self.colors['peach'], label = 'Mouse speed')
                ax.scatter(self.timeax_processed[self.ids_back_wall], self.mouse_speed[self.ids_back_wall], color = 'grey', s=10)
                ax.legend()
                ax.set_xlabel('Time (s)'); ax.set_ylabel('Mouse velocity (cm/s)')
                plt.show()
            
        def get_gait_cycle_boundaries(self, inputlist, interactive = True): # use sign functions as inputs! e.g. self.lHy1_sign
            # get gait cycle times
            inputlist_swing, inputlist_stance = np.asarray(self.find_analysis_window(inputlist, binary = True, filter = False, threshold=15))

            stance_ids = np.where((inputlist_stance>self.trdm_on) & (inputlist_stance<self.trdm_off))[0] # find the ids in inputlist_stance corresponding to trdm on times
            inputlist_stance = inputlist_stance[stance_ids]
            inputlist_stance = np.setdiff1d(inputlist_stance, self.ids_back_wall) # update inputlist_stance to exclude points when mouse is pushed against the back wall

            swing_ids = np.where((inputlist_swing>self.trdm_on) & (inputlist_swing<self.trdm_off))[0]
            inputlist_swing = inputlist_swing[swing_ids]
            inputlist_swing = np.setdiff1d(inputlist_swing, self.ids_back_wall)

            if inputlist_stance[0] > inputlist_swing[0]:
                inputlist_swing = inputlist_swing[1:]
            if inputlist_stance[-1] > inputlist_swing[-1]:
                inputlist_stance = inputlist_stance[:-1]

            return (inputlist_swing, inputlist_stance)
        
        # def polarplot(self):
        #     for k in range(len(self.l))



        

analyser = GaitAnalyser(voltage = 1.25)
analyser.initialise_data()
analyser.track_mouse_speed(videoplot = False, staticplot = False)
analyser.plot_trajectories(videoplot = False, staticplot = False, interactive = True)
#analyser.polarplot()
