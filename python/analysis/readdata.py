#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 10:21:38 2022

@author: aino

Reads bandpower data from csv files and creates a matrix whose rows represent each subject. 
Plots control vs patient grand average and ROI averages. Plots spectra for different tasks and a single subject and channel.
"""

import numpy as np
import os
import csv
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from math import log
from sklearn.preprocessing import scale

# Get the list of subjects
with open('/net/tera2/home/aino/work/mtbi-eeg/python/processing/eeg/subjects.txt', 'r') as subjects_file:
    subjects = subjects_file.readlines()
    subjects_file.close()
    
tasks = [['ec_1', 'ec_2', 'ec_3'], 
         ['eo_1', 'eo_2', 'eo_3'], 
         ['PASAT_run1_1', 'PASAT_run1_2'], 
         ['PASAT_run2_1', 'PASAT_run2_2']]

wide_bands = [(0,3), (3,7), (7,11), (11,34), (34,40), (40,90)] # List of freq. indices (Note: if the bands are changed in 04_bandpower.py, these need to be modified too.)


# Choose normalization methods
channel_scaling = True

# Define which files to read for each subject
chosen_tasks = tasks[0] # Choose tasks (ec: 0, eo: 1, pasat1: 2, pasat2: 3)
subjects_and_tasks = [(x,y) for x in subjects for y in chosen_tasks] # length = subjects x chosen_tasks

# TODO: Choose region of interest (not implemented yet)
region_of_interest = False
channels = []

# Choose frequency bands
# TODO: these do not seem to do anything?? 
change_bands = True 

# Choose what to plot
plot_tasks = False
plot_averages = False

# Choose one channel and subject to be plotted
channel = 59
chosen_subject = '09P'
plot_array = [] # Contains len(chosen_tasks) vectors (length = 89) (89 frequency bands)



# Create a two dimensional list to which the data will be saved
all_bands_vectors = [] # Contains n (n = subjects x chosen_tasks) vectors (length = 5696 = 64 x 89) (64 channels, 89 frequency bands)


# Lists for grand average and ROI
averages_controls = [[], [], []] # Contains 3 lists (all, frontal, occipital)(length = len(chosen_tasks) x controls) of vectors (lenght = 39)(39 frequency bands)
averages_patients= [[], [], []] # all, frontal, occipital
averages_problem = [] #TODO: what is this?


"""
Reading data
"""
# Go through all the subjects
for pair in subjects_and_tasks:
    subject, task = pair[0].rstrip(), pair[1] # Get subject & task from subjects_and_tasks
    bandpower_file = "/net/theta/fishpool/projects/tbi_meg/k22_processed/sub-" + subject + "/ses-01/eeg/bandpowers/" + task + '.csv'
    
    # Create a 2D list to which the read data will be added
    sub_bands_list = [] # n_freq x 64 matrix (64 channels, n_freq frequency bands)
    
    # Read csv file and save the data to f_bands_list
    with open(bandpower_file, 'r') as file:
        reader = csv.reader(file)
        for f_band in reader: #Goes through each frequency band. 
            sub_bands_list.append([float(f) for f in f_band])
        file.close()
        
    # Convert list to array    
    sub_bands_array = np.array(sub_bands_list) # m x n matrix (m = frequency bands, n=channels)
    
    
    if change_bands: #If we want to aggregate 1 Hz freq bands to concentional delta, theta, alpha, etc.
        sub_bands_list = []
        sub_bands_list.append([np.sum(sub_bands_array[slice(*t),:], axis=0) for t in wide_bands])
        #create array again
        sub_bands_array = np.array(sub_bands_list)[0] #apparently there is annyoing extra dimension
    
    if channel_scaling: #Normalize each band
        ch_tot_powers = np.sum(sub_bands_array, axis = 0)
        sub_bands_array = sub_bands_array / ch_tot_powers[None,:]
    
    sub_bands_vec = np.concatenate(sub_bands_array.transpose())
        
    # Add vector to matrix
    all_bands_vectors.append(sub_bands_vec)
        
    """
    For plotting
    """
    # Convert the array to dB
    log_array = 10* np.log10(sub_bands_array)  # 64 x 39 matrix
    
    
    # Plot different tasks for one subject and channel
    if chosen_subject in subject:
        plot_array.append(log_array[:, channel])
    

    # Grand average and ROI 
    sum_all = np.sum(log_array, axis = 1) # Vector (length = 39)
    sum_frontal = np.sum(log_array[:, 0:22], axis = 1) # Vector (length = 39)
    sum_occipital = np.sum(log_array[:, 60:63], axis = 1) # Vector (length = 39)
    
    if 'P' in subject:
        averages_patients[0].append(np.divide(sum_all, 64))
        averages_patients[1].append(np.divide(sum_frontal, 22))
        averages_patients[2].append(np.divide(sum_occipital, 3))
    elif 'C' in subject:
        averages_controls[0].append(np.divide(sum_all, 64))
        averages_controls[1].append(np.divide(sum_frontal, 22))
        averages_controls[2].append(np.divide(sum_occipital, 3))
    else:
        averages_problem.append(subject)
    
"""
Creating a data frame
"""

# Create indices for dataframe
indices = []
for i in subjects_and_tasks:
    i = i[0].rstrip()+'_'+i[1]
    indices.append(i)

# Convert numpy array to dataframe
dataframe = pd.DataFrame(np.array(all_bands_vectors), indices) #n x m matrix where n = subjects x tasks, m = channels x frequency bands

# Add column 'Group'
groups = []
for subject in indices:
    if 'P' in subject[2]:
        groups.append(1)
    elif 'C' in subject[2]:
        groups.append(0)
    else:
        groups.append(2) # In case there is a problem
dataframe.insert(0, 'Group', groups)
subs = np.array([s.split('_'+chosen_tasks[0][0:3])[0] for s in indices]) #TODO: horrible bubble-gum quickfix for CV problem
#fixed the line above so that it works for all tasks
dataframe.insert(1, 'Subject', subs)

