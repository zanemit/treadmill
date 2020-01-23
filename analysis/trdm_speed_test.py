import os
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
c1 = (102/255, 194/255, 165/255) # colour for plotting

experimenter = 'ZM' # initials
experiment_date = '200115' # format 'YYMMDD'
experiment_type = 'V' # 'V' = videos, 'E' = EMG
dlc_date = 'Jan16' # format month-date like the created DLC folder
dlc_iters = '5000'

s = 'DeepCut_resnet50_DLC' + dlc_date + 'shuffle1_' + dlc_iters

"""
        ############## EXPERIMENT CONFIG  ####################
"""
