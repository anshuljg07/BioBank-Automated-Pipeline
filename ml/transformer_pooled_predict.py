# -*- coding: utf-8 -*-
"""
Created on Sun Jul 31 17:05:30 2022

@author: adityabiswas
"""
import math
import pandas as pd
import numpy as np
import re
import warnings

import torch
from torch.nn.functional import binary_cross_entropy
from transformers import AutoTokenizer, AutoModel

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score as AUC
from sklearn.utils.class_weight import compute_class_weight

###############################################################################
##### Helper functions to create document embeddings

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[\r\n]+', ' ', text) # remove line breaks and stuff
    text = re.sub(r'[^\x00-\x7F]+', ' ', text) # remove special characters
    return text



def get_doc_split_indices(doc_token_len, max_len = 126, min_overlap = 0.2):
    # finds indices that would split a document into sub-documents
    # each with at least min_overlap percent tokens shared with the previous subdoc
    
    if doc_token_len <= max_len: # only one group required
        indices = np.array([0, doc_token_len], dtype = int)[None,:]
        return indices
    
    else: # more than 1 group required
        
        # one group for the first 126 tokens (explaining '- max_len' and later '+ 1')
        # a group for subsequent new tokens, of size 80% of 126 ((1-min_overlap)*max_len)
        #           (in addition to 20% overlap from last group)
        n_groups = math.ceil((doc_token_len-max_len)/((1-min_overlap)*max_len)) + 1
        
        # first col is start index for group, second is stop
        indices = np.empty((n_groups, 2), dtype = int)
        indices[0,0] = 0
        
        # recalculate overlap percentage to maximize overlap given number of groups
        #          i.e. solve equation above for overlap, removing the ceiling function
        eps = 1e-6 # add to prevent numerical instabilities downstream
        non_overlap = 1/((n_groups - 1)*max_len/(doc_token_len-max_len)) + eps
        
        # set start index for each group to be approx 80% of 126 more than last group
        # need to keep track of remainders to make sure all doc_token_indices
        #                   are accounted for
        remainder = 0
        for j in range(1,n_groups):
            increment = int(math.floor(max_len*non_overlap))
            remainder += max_len*non_overlap - increment
            indices[j,0] = indices[j-1,0] + increment
            add_one = math.floor(remainder) > 0
            if add_one:
                indices[j,0] += 1
                remainder -= 1
        
        # stop index is set so each group is length max_len
        indices[:,1] = indices[:,0] + max_len
    
        assert indices[-1,1] == doc_token_len # if this fires, there is an error above
        return indices
    

def batch_tokenize(text, tokenizer, max_len = 128, min_overlap = 0.2):
    # Tokenizes a document and then splits it into a batch of tokens,
    # each of length 128.  Each group of tokens overlaps with the previous
    # and next group, and has its own stop/start tokens
    # Documents shorter than 128 tokens are padded
    
    doc_tokenized = tokenizer(text, 
                              add_special_tokens = False, # dont add start/stop tokens
                              return_tensors = 'pt') # in pytorch format
    
    # split tokenized sentence into overlapping groups of 126 tokens
    #                           (i.e. EXCLUDING stop and start tokens)
    # NOTE: nothing effectively happen if less than 126 tokens total
    doc_token_len = doc_tokenized['input_ids'].size()[1]    
    split_indices = get_doc_split_indices(doc_token_len, 
                                          max_len = max_len-2, 
                                          min_overlap = min_overlap)
    for key in doc_tokenized:
        doc_tokenized[key] = torch.cat([doc_tokenized[key][:,start:stop] \
                                        for (start,stop) in split_indices],
                                       dim = 0)
        
        
    # add stop and start tokens back in manually
    n_groups = len(split_indices) 
    special_ones = torch.ones((n_groups, 1)).long()
    special_values = {'input_ids': [101, 102], 'token_type_ids': [0,0],
                      'attention_mask': [1,1]}
    for key in doc_tokenized:
        doc_tokenized[key] = torch.cat([special_ones*special_values[key][0],
                                        doc_tokenized[key],
                                        special_ones*special_values[key][1]],
                                       dim = 1)
        
        
    # do zero-padding if less than 128 tokens total
    if n_groups == 1:
        special_zeros = torch.zeros((1, max_len-(split_indices[0,1]+2))).long()
        for key in doc_tokenized:
            doc_tokenized[key] = torch.cat([doc_tokenized[key], special_zeros], 
                                           dim = 1)
        
    return doc_tokenized


def compute_split_agg(tensor, split_lengths, func, dim = 0):
    # split lengths needs to be tuple/list, not tensor
    # used to create aggregations over sub documents, like maxes or means
    tensor_split = torch.split(tensor, split_lengths, dim = dim)
    tensor_split = [func(x, dim).unsqueeze(dim) for x in tensor_split]
    return torch.cat(tensor_split, dim = dim)
    

###############################################################################
##### Load dataset and embedding model

tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
embedding_model = AutoModel.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")


df = pd.read_csv("H:/Data/NLP Clinical Text Analysis/Dennis Project/data_cleaned.csv",
                 index_col = 'sequenceno')
labels_numpy = df['labels'].values
labels_torch = torch.from_numpy(labels_numpy).float()


###############################################################################
##### Split sentences, tokenize, and do embeddings

max_length_tokens = 128
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
    masks_torch.append(doc_tokenized['attention_mask'])
    if ((i+1) % 10 == 0) | ((i+1) == len(df)):
        print("Document {0} / {1} complete".format(i+1, len(df)))

# create mean embeddings in numpy arrays
# this would only be used to create a simple mean-embedding model
#                           to compare our main approach against
embeddings_torch_tensor = torch.cat(embeddings_torch, dim = 0)
masks_torch_tensor = torch.cat(masks_torch, dim = 0)
row_token_means = torch.sum(embeddings_torch_tensor*masks_torch_tensor.unsqueeze(2), dim = 1)
row_token_means /= torch.sum(masks_torch_tensor, dim = 1).unsqueeze(1)
embeddings_mean = compute_split_agg(row_token_means, subdoc_lengths,
                                    func = torch.mean, dim = 0)
embeddings_mean_numpy = embeddings_mean.numpy()

# wrap original lists from loop in np.array to make them indexable
# this is so we can easily index by document, rather than by subdocument
# this throws a warning rn, so may not work correctly in the future, but works correctly now
warnings.simplefilter(action = 'ignore', category = FutureWarning)
embeddings_torch = np.array(embeddings_torch, dtype = 'object')
masks_torch = np.array(masks_torch, dtype = 'object')
subdoc_lengths = np.array(subdoc_lengths)



###############################################################################
##### Neural Network custom classes and functions

class Embedding_Pooled_Classifier(torch.nn.Module):
    # this model performs a linear mapping on each embedded word in each subdocument
    # then it performs softmax pooling over the word mappings within each subdocument
    # then it performs softmax pooling over subdocument mappings for each document
    # this result is passed through the logistic fxn to make a prediction for each doc
    #
    # a temperature parameter is learned to tune the softmax pooling between
    #                                           average pooling and max pooling
    def __init__(self, embedding_size, n_labels = 1):
        super().__init__()
        self.linear = torch.nn.Linear(in_features = embedding_size,
                                      out_features = n_labels)
        torch.nn.init.xavier_uniform_(self.linear.weight, gain = 0.01)
        
        
        self.log_temperature = torch.nn.Parameter(torch.zeros(1) - 2)        
    
    def forward(self, embeddings, subdoc_lengths):
        z = self.linear(embeddings).squeeze(2)
        z_pool_words = self.softmax_pool(z, dim = 1)
        z_pool_subdocs = compute_split_agg(z_pool_words, 
                                           subdoc_lengths, 
                                           func = lambda x,d: self.softmax_pool(x,d),
                                           dim = 0)
        y_hat = torch.sigmoid(z_pool_subdocs)
        return y_hat
    
    def softmax_pool(self, x, dim):
        temperature = torch.exp(self.log_temperature)
        return torch.sum(x*torch.softmax(temperature*x, dim = dim), dim = dim)

    def evaluate_AUROC(self, X_val, subdoc_lengths_val, y_val):
        self.eval()
        y_val_hat = self.forward(X_val, subdoc_lengths_val).detach()
        performance = AUC(y_val.numpy(), y_val_hat.numpy())
        self.train()
        return performance
    

class LinearScheduler(object):
    # linearly updates learning rate from stop to start over 
    # a fixed, pre-specified number of iterations
    def __init__(self, optimizer, start, stop, num_iters):
        self.optimizer = optimizer
        self.inc = (stop - start)/(num_iters-1)
        self.counter = 0
        self.num_iters = num_iters
        self.raised_warning = False
        
    def step(self):
        self.counter += 1
        if self.counter < self.num_iters:
            self.optimizer.param_groups[0]['lr'] += self.inc
        elif self.counter == self.num_iters:
            pass
        else:
            if not self.raised_warning:
                warnings.warn("Scheduler has already finished its last iteration.\n No further learning rate changes will be made.")
                self.raised_warning = True
            
            
def train_model(train_index, val_index, epochs, embedding_size, n_labels = 1,
                print_every = None, alpha = 0.01, lr_start = 0.1):
    # decide whether to print to console or not
    if (print_every is None) or (print_every <= 0):
        verbose = False
        print_every = 1 # to prevent division by 0 downstream
    else:
        verbose = True
    
    # split data up
    # we skip the attention masks, since we don't actually need them for this problem
    # but attention masks may become necessary in future NLP problems with shorter text
    X_train = list(embeddings_torch[train_index])
    X_train = torch.cat(X_train, dim = 0)
    X_val = list(embeddings_torch[val_index])
    X_val = torch.cat(X_val, dim = 0)
    subdoc_lengths_train = list(subdoc_lengths[train_index])
    subdoc_lengths_val = list(subdoc_lengths[val_index])
    y_train = labels_torch[train_index]
    y_val = labels_torch[val_index]
    
    
    # make model
    model = Embedding_Pooled_Classifier(embedding_size, n_labels)
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
    weights = weights[torch.arange(len(y_train)),y_train.long()]
    
    # creatining this fxn is necessary to use LFBGS optimizer
    # essentially defines the full forward and backward passes
    def closure():
        optimizer.zero_grad()
        y_train_hat = model(X_train, subdoc_lengths_train)
        loss_data = binary_cross_entropy(y_train_hat, y_train, weight = weights)
        loss_reg = alpha*torch.abs(model.linear.weight).mean()
        loss = loss_data + loss_reg
        loss.backward()
        return loss_data.data.item()
    
    
    # model training loop
    # note that we use FULL batches here rather than minibatches
    # thus, apart from the initialization, the optimization is deterministic
    running_loss = 0
    epoch_print_code = "0" + str(len(str(epochs))) + "d"
    for epoch in range(1,epochs+1):
        running_loss += optimizer.step(closure)
        scheduler.step()
        
        # print info to console
        if (epoch % print_every == 0) and verbose:
            train_auc = model.evaluate_AUROC(X_train, subdoc_lengths_train, y_train)
            val_auc = model.evaluate_AUROC(X_val, subdoc_lengths_val, y_val)
            running_loss_mean = running_loss/print_every
            running_loss = 0
            print(("Epoch: {0:" + epoch_print_code + \
                   "}  |  Loss: {1:.4f}  |  Train AUC: {2:.3f}  | Val AUC: {3:.3f}").format(\
                        epoch,
                        running_loss_mean,
                        train_auc,
                        val_auc))

    
    # record validation performance and return
    performance = model.evaluate_AUROC(X_val, subdoc_lengths_val, y_val)
    globals().update(locals()) # BAD! only here right now for convenient scripting
    return performance


###############################################################################
##### Training/Eval Loop


training_args = {"embedding_size": embeddings_torch[0].size()[-1],
                 "n_labels": 1,
                 "epochs": 20,
                 "print_every": 5, # makes training verbose, prints every 5 epochs
                 "alpha": 3, # l1 regularization parameter for linear.weight
                 "lr_start": 0.01}  # lr linearly approaches 1 from this value with each successive epoch

globals().update(training_args) # put in global namespace for convenience
                 

performances = []
splitter = StratifiedKFold(n_splits = 5, shuffle = True)
for i, indices in enumerate(splitter.split(df,labels_numpy)):
    print("\n===================================")
    print("||     Beginning Iteration {0}     ||".format(i+1))
    print("===================================")
    performance = train_model(*indices, **training_args)
    print("---------------------------")
    print("Final Validation AUC: {0:.3f}".format(performance))
    performances.append(performance)

print("\n==========================")
print("Mean Validation AUC: {0:.3f}".format(np.mean(performances)))
print("==========================")



