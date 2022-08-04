# -*- coding: utf-8 -*-
"""
Created on Sun Jul 31 17:05:30 2022

@author: adityabiswas
"""

import pandas as pd
import numpy as np
import warnings

from document_preprocessing import clean_text, batch_tokenize
from document_preprocessing import subdoc_lengths_to_indices

from nn_text_classification import EmbeddingPooledClassifier, LinearScheduler, l1_reg


import torch
from torch.nn import BCEWithLogitsLoss
from transformers import AutoTokenizer, AutoModel

from sklearn.model_selection import StratifiedKFold
from sklearn.utils.class_weight import compute_class_weight


###############################################################################
##### Load dataset and embedding model

tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
embedding_model = AutoModel.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")


df = pd.read_csv("H:/Data/NLP Clinical Text Analysis/Dennis Project/data_cleaned.csv",
                 index_col = 'sequenceno')
label_name = 'tubulitis'
labels_numpy = df[label_name].values
labels_torch = torch.from_numpy(labels_numpy).float()


###############################################################################
##### Split sentences, tokenize, and do embeddings

max_length_tokens = 512
min_overlap = 0.2

embeddings_torch = []
masks_torch = []
subdoc_lengths = []
print("\nEmbedding Documents")
print("--------------------")
for i in range(len(df)):
    # clean each document, split it into a batch of subdocuments, 
    # tokenize each, and finally embed each
    doc_text = clean_text(df['text'].iloc[i])
    doc_tokenized = batch_tokenize(doc_text, tokenizer,
                                   max_len = max_length_tokens,
                                   min_overlap = min_overlap)
    embedding = embedding_model(**doc_tokenized)[0].detach()
    
    # record relevant info and print
    embeddings_torch.append(embedding)
    subdoc_lengths.append(embedding.size()[0])
    masks_torch.append(doc_tokenized['attention_mask'] == 1)
    if ((i+1) % 10 == 0) | ((i+1) == len(df)):
        print("Document {0} / {1} complete".format(i+1, len(df)))


# wrap original lists from loop in np.array to make them indexable
# this is so we can easily index by document, rather than by subdocument
# this throws a warning rn, so may not work correctly in the future, but works correctly now
warnings.simplefilter(action = 'ignore', category = FutureWarning)
embeddings_torch = np.array(embeddings_torch, dtype = 'object')
masks_torch = np.array(masks_torch, dtype = 'object')
subdoc_lengths = torch.Tensor(subdoc_lengths).long()



###############################################################################
##### Training Function
            

def train_model(train_index, val_index, epochs, embedding_size, n_labels = 1,
                print_every = None, alpha = 0.01, lr_start = 0.1, temperature_init = 1):
    # decide whether to print to console or not
    if (print_every is None) or (print_every <= 0):
        verbose = False
        print_every = 1 # to prevent division by 0 downstream
    else:
        verbose = True
        
    assert n_labels == 1 # not configured to work with more than 1 label yet
    
    # split data up
    # full_data tensors are pulled from global variables
    X_train = torch.cat(list(embeddings_torch[train_index]), dim = 0)
    X_val = torch.cat(list(embeddings_torch[val_index]), dim = 0)
    attn_masks_train = torch.cat(list(masks_torch[train_index]), dim = 0)
    attn_masks_val = torch.cat(list(masks_torch[val_index]), dim = 0)
    subdoc_indices_train = subdoc_lengths_to_indices(subdoc_lengths[train_index])
    subdoc_indices_val = subdoc_lengths_to_indices(subdoc_lengths[val_index])
    y_train = labels_torch[train_index]
    y_val = labels_torch[val_index]
    
    
    # make model
    model = EmbeddingPooledClassifier(embedding_size = embedding_size, 
                                        n_labels = n_labels,
                                        temperature_init = temperature_init)
    optimizer = torch.optim.LBFGS(model.parameters(), 
                                  lr = lr_start)
    scheduler = LinearScheduler(optimizer, 
                                start = lr_start, 
                                stop = 1, 
                                num_iters = epochs)
    
    # make balanced weights for use in loss function
    # i.e. upweight the cost of errors for the rarer class
    class_weight = compute_class_weight(class_weight = 'balanced',
                                        classes = [0,1],
                                        y = y_train.numpy())
    weights = torch.from_numpy(class_weight).unsqueeze(0).repeat(len(y_train),1)
    weights = weights[torch.arange(len(y_train)), y_train.long()]
    loss_fxn_data = BCEWithLogitsLoss(weight = weights)
    
    # creatining this fxn is necessary to use LFBGS optimizer
    # essentially defines the full forward and backward passes
    def closure():
        optimizer.zero_grad()
        y_logit_train_hat = model(X_train, subdoc_indices_train, attn_masks_train)
        loss_data = loss_fxn_data(y_logit_train_hat, y_train) # binary cross entropy
        loss_reg = alpha*l1_reg(model.linear.weight)
        loss = loss_data + loss_reg
        loss.backward()
        return loss_data.data.item() # return for printing
    
    
    # model training loop
    # note that we use FULL batches here rather than minibatches
    # thus, apart from the initialization, the optimization is deterministic
    running_loss = 0
    epoch_print_code = "0" + str(len(str(epochs))) + "d"
    for epoch in range(1,epochs+1):
        running_loss += optimizer.step(closure) # loss only from data, not reg
        scheduler.step()
        
        # print info to console
        if (epoch % print_every == 0) and verbose:
            train_auc = model.evaluate_AUROC(X_train, subdoc_indices_train, 
                                             attn_masks_train, y_train)
            val_auc = model.evaluate_AUROC(X_val, subdoc_indices_val,
                                           attn_masks_val, y_val)
            running_loss_mean = running_loss/print_every
            running_loss = 0
            print(("Epoch: {0:" + epoch_print_code + \
                   "}  |  Loss: {1:.4f}  |  Train AUC: {2:.2f}  | Val AUC: {3:.3f}").format(\
                        epoch,
                        running_loss_mean,
                        train_auc,
                        val_auc))

    
    # record validation performance and return
    performance = model.evaluate_AUROC(X_val, subdoc_indices_val, attn_masks_val, y_val)
    globals().update(locals()) # BAD! only here right now for convenient scripting
    return performance



###############################################################################
##### Training/Eval Loop


training_args = {"embedding_size": embeddings_torch[0].size(-1),
                 "n_labels": 1, # only configured to accept 1 at the moment
                 "epochs": 30,
                 "print_every": 5, # makes training verbose, prints every 5 epochs
                 "alpha": 3, # l1 regularization parameter for linear.weight
                 "lr_start": 0.01,  # lr linearly approaches 1 from this value with each successive epoch
                 "temperature_init": 0} # biases softmax pooling towards averaging at start of training

globals().update(training_args) # put in global namespace for convenience
                 

performances = []
splitter = StratifiedKFold(n_splits = 5, shuffle = False)
for i, cv_indices in enumerate(splitter.split(df,labels_numpy)):
    print("\n===================================")
    print("||     Beginning Iteration {0}     ||".format(i+1))
    print("===================================")
    performance = train_model(*cv_indices, **training_args)
    print("---------------------------")
    print("Final Validation AUC: {0:.3f}".format(performance))
    performances.append(performance)

print("\n==========================")
print("Mean Validation AUC: {0:.3f}".format(np.mean(performances)))
print("==========================")


###############################################################################
##### Training details

### for focal glomerulosclerosis
alpha = 3
# avg auc: 0.99

### for focal glomerulosclerosis
alpha = 3
# avg auc: 0.95
# lots of numerical instabilities and still v dependent on init

### for eosinophils
alpha = 3
# avg auc: 0.97

### for tubulitis
alpha = 3
# avg auc: 0.944


