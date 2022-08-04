# -*- coding: utf-8 -*-
"""
Created on Wed Aug  3 22:21:46 2022

@author: adityabiswas
"""

import math
import numpy as np
import re

import torch

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
    # Tokenizes a document and then splits it into a batch of tokens, each item
    #       representing a subdocument and consisting of 128 (or max_len) tokens
    # Each group of tokens overlaps with the previous and next group, and 
    #       has its own stop/start tokens
    # Documents shorter than 128 tokens are right zero-padded to 128 tokens
    
    doc_tokenized = tokenizer(text, 
                              add_special_tokens = False, # dont add start/stop tokens
                              return_tensors = 'pt') # in pytorch format
    
    # split tokenized sentence into overlapping groups of 126 tokens
    #                           (i.e. EXCLUDING stop and start tokens)
    # NOTE: nothing effectively happens if less than 126 tokens total
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
        n_pad_tokens = max_len - (split_indices[0,1] + 2)
        special_zeros = torch.zeros((1, n_pad_tokens)).long()
        for key in doc_tokenized:
            doc_tokenized[key] = torch.cat([doc_tokenized[key], special_zeros], 
                                           dim = 1)
        
    return doc_tokenized


def compute_split_agg(tensor, split_lengths, dim = 0, func = torch.mean):
    # NOTE: this fxn is probably not necessary.  we can do this more efficiently
    # using the torch_scatter package (see ParameterizedSoftmaxPooling for an implementation)
    
    # split lengths needs to be tuple/list, not tensor
    # used to create aggregations over sub documents, like maxes or means
    # need to use a lambda func if "dim" is not 2nd positional argument naturally
    # accordingly, when using a lambda func, need to include aggregation dim as second arg
    tensor_split = torch.split(tensor, split_lengths, dim = dim)
    tensor_split = [func(x, dim).unsqueeze(dim) for x in tensor_split]
    return torch.cat(tensor_split, dim = dim)


def subdoc_lengths_to_indices(subdoc_lengths):
    # returns a vector the length of the number of total subdocuments
    # where each element is an index for which document the subdoc belongs to
    # (docs in given order are associated with indices 0,1,2,3,4,...)
    return torch.repeat_interleave(torch.arange(len(subdoc_lengths)), subdoc_lengths)

def create_numpy_mean_embeddings(embeddings_torch, masks_torch, subdoc_lengths):
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
    return embeddings_mean_numpy
    
