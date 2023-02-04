"""
Copyright by Verna Heikkinen 2022
 
Script for plotting ROC and computing AUC for mTBI classification results on EEG data

Works from commandline:
    %run ROC_AUC.py --task eo --clf SVM
"""
#
import os
import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt

#sfrom sklearn import preprocessing
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, StratifiedGroupKFold, LeaveOneOut, GroupKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve, roc_auc_score, RocCurveDisplay, auc
#from sklearn.covariance import OAS
from readdata import dataframe, tasks #TODO: would want to decide which tasks are used


def Kfold_CV_solver(solver, X, y, groups, folds):
    
    skf = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=20)
    split = skf.split(X, y, groups) #takes into account the groups (=subjects) when splitting the data
    
    tprs = [] #save results for plotting
    aucs = []
    mean_fpr = np.linspace(0, 1, 100)
    
    for train_index, test_index in split:
        
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
    
        if solver == "LDA":
            clf = LinearDiscriminantAnalysis(solver='svd')
        elif solver == "SVM":
            clf = SVC(probability=True)
        elif solver == "LR":
            clf = LogisticRegression(penalty='l1',solver='liblinear',random_state=0)
        elif solver=='RF':
            clf = RandomForestClassifier()
     
        else:
            raise("muumi")


        #clf = make_pipeline(StandardScaler(), clf)
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test).astype(int)
        
        viz = RocCurveDisplay.from_estimator(
        clf,
        X_test,
        y_test,
        name="",
        alpha=0.3,
        lw=1,
        ax=ax,
        )
        interp_tpr = np.interp(mean_fpr, viz.fpr, viz.tpr)
        interp_tpr[0] = 0.0
        tprs.append(interp_tpr)
        aucs.append(viz.roc_auc)

    return test_index, pred, tprs, aucs, mean_fpr


def ROC_results(LOOCV_results):
    """
    A function that fits a classifier to the data using leave-one-out cross-validation,
    computes the ROC and AUC values for each fold.
    
    
    Parameters
    ----------
    CV_results : tuple 
        Results from CV_solver
    
    
    
    Returns
    -------
    
    figure, maybe

    """    
    
    tprs, aucs = LOOCV_results[2], LOOCV_results[3]
    mean_fpr = LOOCV_results[4]
    

    ax.plot([0, 1], [0, 1], linestyle="--", lw=2, color="r", label="Chance", alpha=0.8)

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
        alpha=0.8,
    )

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

    ax.set(
        xlim=[-0.05, 1.05],
        ylim=[-0.05, 1.05],
        title="10-fold CV ROC curve",
    )
    ax.legend(loc="lower right", ncol =2, fontsize=7) 
    ax.set_aspect('equal')



def LOOCV_solver(solver, X, y, groups):
    """
    A function that fits a classifier to the data using leave-one-out cross-validation,
    and computes the ROC and AUC values. Lastly, it plots the results and reurns the plot


    Parameters
    ----------
    solver : string 
        The classifier used to perform the analysis
    X : numpy array
        The data array
    y : numpy array
        The classes / binary response variable
    group : series
        Maps each observation to correct subject


    Returns
    -------
    Nothin' 

    """
    gkf = GroupKFold(n_splits=len(pd.unique(groups)))
    folds = gkf.split(X, y, groups=groups) #create loo folds (here loo -> leave each subj. out)
        
    
    tprs = [] #save results for plotting
    aucs = []
    all_probs = [] #save the probabilities in a list
    ys = [] #save all responses 
    mean_fpr = np.linspace(0, 1, 100)
    
    for train_ids, test_ids in folds:
    
        if solver == "LDA":
            clf = LinearDiscriminantAnalysis(solver='svd')
        elif solver == "SVM":
            clf = SVC(probability=True)
        elif solver == "LR":
            clf = LogisticRegression(penalty='l1',solver='liblinear',random_state=0)
        elif solver=='RF':
            clf = RandomForestClassifier()
     
        else:
            raise("muumi")
        X_train = X.iloc[train_ids]
        X_test = X.iloc[test_ids]
        
        y_train = y[train_ids]
        y_test = y[test_ids]
        ys.append(y_test[0]) #pick the first one since we get n_tasks identical labels

        #clf = make_pipeline(StandardScaler(), clf)
        clf.fit(X_train, y_train)
        pred = clf.predict(X_test).astype(int)
        all_probs.append(clf.fit(X_train, y_train).predict_proba(X_test)[:,1])
        
        
    ys = np.array(ys)
    all_probs = np.mean(np.array(all_probs), axis=1)
    
    fpr, tpr, thresholds = roc_curve(ys, all_probs) #calculare roc curve
    roc_auc = auc(fpr, tpr) #get area under curve
    

    ax.plot(fpr, tpr, lw=2, alpha=0.5, color='b', label='LOOCV ROC (AUC = %0.2f)' % (roc_auc))
    ax.plot([0, 1], [0, 1], linestyle='--', lw=2, color='r', label='Chance level', alpha=.8)
    ax.set(
        xlim=[-0.05, 1.05],
        ylim=[-0.05, 1.05],
        title='LOO-CV ROC curve',
        xlabel='False Positive Rate',
        ylabel='True Positive Rate',
    )

    ax.legend(loc="lower right")
    ax.set_aspect('equal')
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    CV = True
    #parser.add_argument('--threads', type=int, help="Number of threads, using multiprocessing", default=1) #skipped for now
    parser.add_argument('--task', type=str, help="ec, eo, PASAT_1 or PASAT_2")
    parser.add_argument('--clf', type=str, help="classifier", default="LR")
    #parser.add_argument('--model', type=str, help="LOOCV or KFOLD", default="KFOLD")
    args = parser.parse_args()
    
    
    #selection_file = f"{args.location}_select_{args.eyes}.csv"
    X, y, group = dataframe.iloc[:,2:dataframe.shape[1]], dataframe.loc[:, 'Group'], dataframe.loc[:, 'Subject']
    
    save_folder = "figures"
    save_file = f"{save_folder}/{args.clf}_{args.task}.pdf"
        

    print(f"TBIEEG classifcation with {args.clf} data on {args.task} task.")
   
    fig, ax = plt.subplots() #TODO: should these be given for the functions?
    
    #if args.model == "KFOLD":
    if CV:
        results = Kfold_CV_solver(solver=args.clf, X=X, y=y, groups=group, folds=10)
        ROC_results(results)
        plt.savefig(fname=save_file)
    #elif args.model=="LOOCV":
    else:
        LOOCV_solver(args.clf, X, y, groups=group)
        plt.savefig(fname=f"{save_folder}/loo-ROC_{args.clf}_{args.task}.pdf")

        

    

