#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 11:58:23 2023

@author: portae1
"""
import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import csv

from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve, accuracy_score, RocCurveDisplay, auc
from sklearn.model_selection import train_test_split, StratifiedGroupKFold, StratifiedKFold
from sklearn.svm import SVC

from statistics import mean, stdev
import logging
logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

# Pseudocode:
    # Read in dataframe and create X, y and groups
    # Split data according to the validation method
    # Output warning if only one class in fold (probability aaaround 26%)
        # If theres only one class in one fold, re-run the split?
    # Test with a new subjects.txt where classes are more unbalanced (e.g., 70-30)
    
    # Fit classifier
    # Cross Validate
    # Return validation results as outputs: true_positives, false_positives, accuracy
    # Would an aggregated confusion matrix from all the splits help out?
    # Plot ROC curves
    # If using the kernel, how should outputs be parsed?
    # Could I run one validation for all 4 models?    
    
#%% Arguments
verbosity = False
# Segments in the chosen task
segments = 3

# Define if we want to use CV with only one segment per subject (and no groups)
one_segment_per_subject = False

## Classifier
#classifier = LinearDiscriminantAnalysis(solver='svd')

# List containing the accuracy of the fit for each split 
accuracies = []

# Interpoling True Positive Rate
interpole_tpr = []

# True Positive RateS
tprs = []
aucs = []
mean_fpr = np.linspace(0, 1, 100)

folds = 5

#%%
# Read in dataframe and create X, y and groups
dataframe = pd.read_csv('dataframe.csv', index_col = 'Index')
## Define features, classes and groups
X = dataframe.iloc[:,2:]
y = dataframe.loc[:, 'Group']
groups = dataframe.loc[:, 'Subject']


#%% 
## (Optional)
    # Define what strategy to use based on the subjects balance

# Note: There is a 27% chance that there's a fold with only one class. This can impact the classifier (especially LDA)
# >>> After 999 iterations, we found 267 folds with 1 class
         
#%% 
 

if one_segment_per_subject == True:
    # TODO: Double check if choosing another segment than the 1st breaks something? It shouldnt
    # Removes (segments-1) rows out of the dataframe X 
    X_one_segment = X[0:len(X):segments]
    y_one_segment = y[0:len(y):segments]
    groups_one_segment = groups[0:len(groups):segments]
    
    # Initialize Stratified K Fold
    skf = StratifiedKFold(n_splits=folds, shuffle=True)
    data_split = skf.split(X_one_segment, y_one_segment, groups_one_segment)
else:
    # Initialize Stratified Group K Fold
    sgkf = StratifiedGroupKFold(n_splits=folds, shuffle=True)
    data_split = sgkf.split(X, y, groups)

# Initialize figure for plottting
fig, ax = plt.subplots(figsize=(6, 6))

# Define classifier
classifier = SVC(probability=True)
for split, (train_index, test_index) in enumerate(data_split):
    # Generate train and test sets for this split
    if one_segment_per_subject == True:
        X_train, X_test = X_one_segment.iloc[train_index], X_one_segment.iloc[test_index]
        y_train, y_test = y_one_segment.iloc[train_index], y_one_segment.iloc[test_index]
    else:
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
     
    logging.info(f'Shape of X_train is {X_train.shape[0]} x {X_train.shape[1]}')
    logging.info(f'Shape of X_test is {X_test.shape[0]} x {X_test.shape[1]}')

    # Fit classifier
    classifier.fit(X_train, y_train)
    
    # Create Receiver Operator Characteristics from the estimator for current split
    viz = RocCurveDisplay.from_estimator(
        classifier,
        X_test,
        y_test,
        drop_intermediate=True,
        name=f"ROC fold {split+1}",
        alpha=1, #transparency
        lw=1, #line width
        ax=ax
    )

    # Predict outcomes
    y_pred = classifier.predict(X_test).astype(int)
    # Estimate accuracy for this split (normalized), and append to list of accuracies
    accuracies.append(accuracy_score(y_test, y_pred))    
    # interpolate to build a series of 'y' values that correspond to linspace 'mean_fpr' 
    interpole_tpr = np.interp(mean_fpr, viz.fpr, viz.tpr)
    # Adds intercept just in case I guess
    interpole_tpr[0] = 0.0
    logging.info(f'AUC for split {split} = {viz.roc_auc}\n')
    tprs.append(interpole_tpr) 
    aucs.append(viz.roc_auc)
    
    # Control if there's only one class in a fold
    values, counts = np.unique(y[test_index], return_counts=True)
    if np.unique(y[test_index]).size == 1:
        logging.warn(f"WARN: Fold {split} has only 1 class! ####")
    elif verbosity == True: 
        fold_size = y[test_index].size
        if counts[0]<=counts[1]:
            print(f"\nFold {split}:")
            print(f'Class balance: {round(counts[0]/fold_size*100)}-{round(100-counts[0]/fold_size*100)}')
        else:
            print(f"\nFold {split}:")
            print(f'Class balance: {round(counts[1]/fold_size*100)}-{round(100-counts[1]/fold_size*100)}')

# plt.scatter(viz.fpr, viz.tpr) shows how this is a step-wise function


# Calculate the mean 
mean_tpr = np.mean(tprs, axis=0)
mean_tpr[-1] = 1.0
mean_auc = auc(mean_fpr, mean_tpr)
std_auc = np.std(aucs)
ax.plot(
    mean_fpr,
    mean_tpr,
    color="b",
    label=r"Mean ROC (AUC = %0.2f $\pm$ %0.2f)" % (mean_auc, std_auc),
    lw=2,
    alpha=0.8
)

# Calculate the mean again
accuracy_average = round(mean(accuracies), 3)
accuracy_std = round(stdev(accuracies), 3)
AUC_mean = round(mean(aucs), 3)
AUC_std = round(stdev(aucs), 3)
print(f"Mean accuracy: {accuracy_average} ± {accuracy_std}\nAUC = {AUC_mean} ± {AUC_std}")

std_tpr = np.std(tprs, axis=0)
tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
ax.fill_between(
    mean_fpr,
    tprs_lower,
    tprs_upper,
    color="grey",
    alpha=0.2,
    label=r"$\pm$ 1 std. dev.",
)

# Plot chance curve
ax.plot([0, 1], [0, 1], "k--", label="Chance level (AUC = 0.5)")

# Labels and axis
ax.set(
    xlim=[-0.05, 1.05],
    ylim=[-0.05, 1.05],
    xlabel="False Positive Rate",
    ylabel="True Positive Rate",
    title="Mean ROC curve with variability\n(Positive label 'Patients')",
)

# Force square ratio plot
ax.axis("square")
# Define legend location
ax.legend(loc="lower right")
plt.show()




# https://www.imranabdullah.com/2019-06-01/Drawing-multiple-ROC-Curves-in-a-single-plot 
# https://scikit-learn.org/stable/auto_examples/model_selection/plot_roc_crossval.html

#  What does roc_curve.from_estimator() object have
#from pprint import pprint
#pprint(vars(viz))
#{'ax_': <matplotlib.axes._subplots.AxesSubplot object at 0x7f15cc85b580>,
# 'estimator_name': 'ROC fold 10',
# 'figure_': <Figure size 432x432 with 1 Axes>,
# 'fpr': array([0.        , 0.11111111, 0.33333333, 0.33333333, 0.44444444,
#       0.44444444, 1.        , 1.        ]),
# 'line_': <matplotlib.lines.Line2D object at 0x7f15cc88b280>,
# 'pos_label': 1,
# 'roc_auc': 0.4814814814814815,
# 'tpr': array([0.        , 0.        , 0.        , 0.58333333, 0.58333333,
#       0.75      , 0.75      , 1.        ])}