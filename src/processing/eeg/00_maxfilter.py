#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 11:48:59 2022

@author: heikkiv

Script that applies maxfiltering on the bidsified data.
Does all tasks in a row. Based on the script by Mia Liljeström.

NOTE: needs to be ran on Maxfilter computer, either manually or via SSH connection (ssh -X ypsilon).
"""

import subprocess
import argparse
import os
from config_eeg import get_all_fnames, fname, tasks

#TODO: maxfilter each task, save to bidsified. IN PROGRESS
#mne.set_log_level('INFO')

cross_talk = '/net/tera2/opt/neuromag/databases/ctc/ct_sparse.fif' #cross-talk correction data file
calibration = '/net/tera2/opt/neuromag/databases/sss/sss_cal.dat' #calibration datafile

#Handle command line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('subject', help='The subject to process')
args = parser.parse_args()

subject = args.subject


all_fnames = zip(
    get_all_fnames(args.subject, kind='raw'), #raw data
    get_all_fnames(args.subject, kind='tsss'), #maxfiltered data
    get_all_fnames(args.subject, kind='tsss_log'), #log files
    get_all_fnames(args.subject, kind='pos') #position file
)


#TODO: another solution is to use MNE version; would that be better??
print("Maxfiltering subject ", args.subject)

for input_f, output_f, log_f, pos_f in all_fnames:
    
    #trans_f = fname.raw(subject=subject, task=tasks[0], run=1)
    trans_f = 'default'
    
    #arguments given to maxfilter program. TODO: check these!
    args = ['/neuro/bin/util/maxfilter', '-f', input_f, '-o', output_f, '-st', '-movecomp', \
            '-autobad','on', '-trans', trans_f, '-ctc', cross_talk, '-cal', calibration, \
            '-hpicons','-origin','fit','-in', '8', '-out', '3', '-frame','head', '-hp', pos_f, '-force', '-v']  
    
    
    #save the error log
    log_output = open(log_f, "w")
    
    # run maxfilter, FIXME
    subprocess.run(args=args, stdout=log_output,stderr=log_output)


