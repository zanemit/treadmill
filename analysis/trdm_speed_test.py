import os
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt
from analysis.analysis_config import Config

#%%
class TrdmAnalyser(Config):
        def __init__(self, posthoc=False):
                plt.ioff()  # make sure plt is not in interactive mode

                Config.__init__(self)
                self.arduino_folder = os.path.join(self.analysis_config["data_folder"], self.analysis_config["experiment_date"]+ "_" + self.analysis_config["experiment_type"] + "_trdm_speed_test")
                self.dlc_folder = os.path.join(self.analysis_config["data_folder"], self.analysis_config["experiment_date"] + "_DLC", "trdm_speed_test")
                self.dlc_file_ext = 'DeepCut_resnet50_DLC' + self.analysis_config["dlc_project_date"] + 'shuffle1_' + self.analysis_config["dlc_iters"]

        def file_name_generator(self, voltage, cam = 'cam0'): 
                filename_h5 = self.analysis_config["experiment_date"] + '_' + str(voltage) + 'V_' + cam + self.dlc_file_ext + '.h5' # dlc file
                filename_csv = self.analysis_config["experiment_date"] + '_' + str(voltage) + 'V_analoginputs.csv' # trdm speed output file
                return (filename_h5, filename_csv)
        
        # extracts x y coordinates of the tape roll
        def extract_h5(self, filename):
                data = pd.read_hdf(filename)
                x = np.asarray(data[self.dlc_file_ext]['side']['x'])
                y = np.asarray(data[self.dlc_file_ext]['side']['y'])
                return (x, y)

        # extracts speed data and timestamp
        def extract_csv(self, filename):
                data = pd.read_csv(filename)
                speed_data = np.asarray(data['trdmSpeed'])*100 # returns treadmill speed in cm/s
                timestamp = np.asarray(data['bsCam_timestamp']) # returns timestamp in nanoseconds
                return (speed_data, timestamp)
        
        def find_test_windows(self, input_list, threshold): # finds windows where the tape is moving at treadmill speed; requires rolling average as input
        # threshold = how many consecutive points should be increasing for it to count as event onset
                i_test_list = []
                for i in range(len(input_list)-threshold):
                        k_test_list = []
                        for k in range(i,i+threshold-1):
                                k_test_list.append(input_list[k+1] > input_list[k])
                        if np.all(k_test_list):
                                i_test_list.append(i)
                start_ids = [i_test_list[0]]
                for z in range(1,len(i_test_list)):
                        if (i_test_list[z]-i_test_list[z-1] != 1):
                                start_ids.append(i_test_list[z])
                end_ids = []
                for z in range(len(i_test_list)-1):
                        if (i_test_list[z+1]-i_test_list[z] != 1):
                                end_ids.append(i_test_list[z]+threshold-5)
                end_ids.append(i_test_list[-1]+threshold-5)
                return (start_ids, end_ids)

        def delta(self, input_list):
                delta_list = []
                for i in range(len(input_list)-1):
                        delta = input_list[i+1] - input_list[i]
                        delta_list.append(delta)
                return np.asarray(delta_list)

        def rolling_average(self, input_list): # rolls over 5
                averaged_list = [input_list[0], np.mean(input_list[0:2]), np.mean(input_list[0:3]), np.mean(input_list[0:4]), np.mean(input_list[0:5])]
                for i in range(6,len(input_list)):
                        element = np.mean(input_list[(i-5):i])
                        averaged_list.append(element)
                return np.asarray(averaged_list)
        
        def plot_trdm_readouts(self, voltage_list):
                b1,a1 = butter(2, 5, btype='low', fs=200)
                b2,a2 = butter(2, 1, btype='low', fs=200)
                os.chdir(self.arduino_folder)
                for voltage in voltage_list:
                        trdm_speed, timestamp = self.extract_csv(self.file_name_generator(voltage)[1])
                        timestamp = timestamp/(10**9) # in seconds

                        #trdm_speed_rolling = rolling_average(trdm_speed)
                        trdm_speed_highfiltered = filtfilt(b1,a1, trdm_speed)
                        t_start = self.find_test_windows(trdm_speed_highfiltered, 60)[0]
                        trdm_speed_lowfiltered = filtfilt(b2,a2,trdm_speed)
                        t_start = t_start[np.where(np.asarray(t_start)>500)[0][0]]
                        timestamp = timestamp[(t_start-200):]
                        timestamp = np.linspace(0,(timestamp[-1]-timestamp[0]),len(timestamp))
        
                        plt.plot(timestamp, trdm_speed_lowfiltered[(t_start-200):], label = '{} V'.format(voltage))
                        #plt.scatter(t_start,trdm_speed_lowfiltered[t_start], color = 'black')
                        plt.legend(ncol=2, title = 'Treadmill input voltage')
        
                        plt.ylim(0,100)
                        plt.xlabel('Time (s)')
                        plt.ylabel('Treadmill speed readout (cm/s)')
                plt.show()
        
        def plot_all_comparisons(self, voltage_list, cam = 'cam1', appendix = 'analoginputs'): # for len(voltage_list)=20
                f, axarr = plt.subplots(10, 4, figsize=(40, 400)) 
                for voltage in voltage_list:
                    os.chdir(self.dlc_folder) # sets directory 1
                    xcoords = self.extract_h5(self.file_name_generator(voltage, cam)[0])[0]
        
                    os.chdir(self.arduino_folder) # sets directory 2
                    trdm_speed, timestamp = self.extract_csv(self.file_name_generator(voltage)[1])
                    xcoords_rolling = self.rolling_average(xcoords)
                    trdm_speed_rolling = self.rolling_average(trdm_speed)
        
                    start_ids, end_ids = self.find_test_windows(xcoords_rolling, 50) # selects test windows
        
                    xcoords_delta = self.delta(xcoords_rolling)*18/1013 # calculates cm moved in x per frame
                    timestamp_delta = self.delta(timestamp)/(10**9) # calculates seconds per frame
                    movement_speed = xcoords_delta / timestamp_delta[:-1]

                    if voltage*10 % 5 != 0:
                        axarr[int(voltage*10//5), 0].plot(xcoords_rolling, color = 'navy', label = 'X coordinates')
                        axarr[int(voltage*10//5), 0].scatter(start_ids, xcoords_rolling[start_ids], color = 'orange')
                        axarr[int(voltage*10//5), 0].scatter(end_ids, xcoords_rolling[end_ids], color = 'red')
                        axarr[int(voltage*10//5), 0].set_title('{} V'.format(voltage))
            
                        for k in range(len(start_ids)):
                            axarr[int(voltage*10//5), 1].plot(movement_speed[start_ids[k]:end_ids[k]], color=self.colors['aqua'], label = 'Object speed')
                            axarr[int(voltage*10//5), 1].plot(trdm_speed_rolling[start_ids[k]:end_ids[k]], color='black', label = 'Speed readout')
        
                    if voltage*10 % 5 == 0:
                        axarr[int(voltage*10//5)-1, 2].plot(xcoords_rolling, color = 'navy')
                        axarr[int(voltage*10//5)-1, 2].scatter(start_ids, xcoords_rolling[start_ids], color = 'orange')
                        axarr[int(voltage*10//5)-1, 2].scatter(end_ids, xcoords_rolling[end_ids], color = 'red')
                        axarr[int(voltage*10//5)-1, 2].set_title('{} V'.format(voltage))
            
                        for k in range(len(start_ids)):
                            axarr[int(voltage*10//5)-1, 3].plot(movement_speed[start_ids[k]:end_ids[k]], color=self.colors['aqua'], label = 'Object speed')
                            axarr[int(voltage*10//5)-1, 3].plot(trdm_speed_rolling[start_ids[k]:end_ids[k]], color='black', label = 'Speed readout')
                plt.show()

        def plot_one_comparison(self, voltage, cam = 'cam1', trial_nr = 1): # trial_br - which tape roll traversion to plot
                os.chdir(self.dlc_folder) # sets directory 1
                xcoords = self.extract_h5(self.file_name_generator(voltage, cam)[0])[0]
    
                b1,a1 = butter(2, 20, btype='low', fs=200)
        
                os.chdir(self.arduino_folder) # sets directory 2
                trdm_speed, timestamp = self.extract_csv(self.file_name_generator(voltage)[1])
                xcoords_rolling = self.rolling_average(xcoords)
                #xcoords_rolling = filtfilt(b2,a2, xcoords)
                trdm_speed_rolling = filtfilt(b1,a1, trdm_speed)
        
                start_ids, end_ids = self.find_test_windows(xcoords_rolling, 50) # selects test windows
    
                xcoords_delta = self.delta(xcoords_rolling)*18/1013 # calculates cm moved in x per frame
                timestamp_delta = self.delta(timestamp)/(10**9) # calculates seconds per frame
                movement_speed = xcoords_delta / timestamp_delta[:-1]
    
                xcoords_error = self.delta(xcoords_rolling)*1/963 # calculates cm moved in x per frame
                movement_error = xcoords_error/timestamp_delta[:-1]
                movement_error = filtfilt(b1,a1,movement_error)
    
                movement_speed = filtfilt(b1,a1, movement_speed)

                f,ax = plt.subplots(1,2)
                ax[0].plot(xcoords_rolling, color ='navy')
                ax[0].scatter(start_ids, xcoords_rolling[start_ids], color = 'orange')
                ax[0].scatter(end_ids, xcoords_rolling[end_ids], color = 'red')
                ax[0].set_xlabel('Timeframe')
                ax[0].set_ylabel('x coordinate (px)')
    
                ax[1].plot(movement_speed[start_ids[trial_nr]:end_ids[trial_nr]], color=self.colors['aqua'],label = 'Object speed')
                ax[1].plot(trdm_speed_rolling[start_ids[trial_nr]:end_ids[trial_nr]], color='black', label = 'Speed readout')
                ax[1].legend()
                ax[1].set_xlabel('Timeframe')
                ax[1].set_ylabel('Speed (cm/s)')
                ax[1].fill_between(range(0, len(movement_speed[start_ids[trial_nr]:end_ids[trial_nr]])), movement_speed[start_ids[trial_nr]:end_ids[trial_nr]] - movement_error[start_ids[trial_nr]:end_ids[trial_nr]],movement_speed[start_ids[trial_nr]:end_ids[trial_nr]] + movement_error[start_ids[trial_nr]:end_ids[trial_nr]], color = 'lightgrey')
    
                f.suptitle('{} V'.format(voltage))
                plt.show()
    
#%%
analyser = TrdmAnalyser()
#analyser.plot_trdm_readouts([0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.25,2.5,2.75,3.0,3.25,3.5,3.75,4.0,4.25,4.5,4.75,5.0])
#analyser.plot_all_comparisons([0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.25,2.5,2.75,3.0,3.25,3.5,3.75,4.0,4.25,4.5,4.75,5.0])
analyser.plot_one_comparison(0.25, trial_nr = 1)
