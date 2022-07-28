# -*- coding: utf-8 -*-
"""
Created on Thu Jul 28 15:10:37 2022

@author: adityabiswas
"""

import collections.abc
collections.Iterable = collections.abc.Iterable # manual import since python version issues
import torch
from simpletransformers.language_representation import RepresentationModel
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.linear_model import LogisticRegression as LR
from sklearn.linear_model import PoissonRegressor as PR
from sklearn.metrics import roc_auc_score as AUC
import numpy as np

###############################################################################
##### Import data

df = pd.read_csv("H:/Data/NLP Clinical Text Analysis/Dennis Project/data_cleaned.csv",
                 index_col = 'sequenceno')


###############################################################################
##### Construct Embeddings


if torch.cuda.is_available():
    device = torch.device('cuda')
    print('There are %d GPU(s) available.' % torch.cuda.device_count())
    print('We will use the GPU:', torch.cuda.get_device_name(0))
    usingCUDA = True
else:
    print('No GPU available, using the CPU instead.')
    usingCUDA = False



model_embedding = RepresentationModel(
                    model_type='bert',
                    model_name='emilyalsentzer/Bio_ClinicalBERT',
                    use_cuda=usingCUDA,  # if using google collab's GPU, set this equal to True
)
    


embedding = model_embedding.encode_sentences(df['text'], combine_strategy='mean')
labels = df['labels'].values


###############################################################################
##### Train model



performance = []
splitter = KFold(n_splits = 5, shuffle = True)
for i, (train_index, val_index) in enumerate(splitter.split(df)):
    X_train, X_val = embedding[train_index,:], embedding[val_index,:]
    y_train, y_val = labels[train_index], labels[val_index]
    
    model = LR(C = 10000, class_weight = 'balanced', max_iter = 1000)
    #model = PR(alpha = 0.001, max_iter = 1000)
    model.fit(X_train, y_train)
    
    y_val_hat = model.predict_proba(X_val)[:,1]
    performance.append(AUC(y_val, y_val_hat))
    print(i)
    
print(np.mean(performance))
