# -*- coding: utf-8 -*-
"""
Created on Wed Aug  3 22:28:13 2022

@author: adityabiswas
"""

import warnings
import torch
from torch_scatter import segment_coo
from torchmetrics.functional import auroc as AUC
###############################################################################
##### Neural Network custom classes and functions

class ParametricSoftmaxPool(torch.nn.Module):
    def __init__(self, temperature_init = 1):
        super().__init__()
        self.temperature = torch.nn.Parameter(torch.Tensor([temperature_init]))        
        
    def forward(self, x, dim, mask = None, group_indices = None):
        h = self.temperature*x
        
        # zeros out softmax where mask is present
        # mask should be boolean
        if mask is not None:
            h[~mask] = -float("Inf") 
        
        # without any grouping, simple fxn
        if group_indices is None:
            return torch.sum(x*torch.softmax(h, dim = dim), dim = dim)
        else:
            # uses segment_csr fxn from pkg torch_scatter
            # assumes group_indices are sorted, with each item identifying
            #                                the group the row belongs to
            
            # add extra dims for compatability with segment_coo fxn and torch.gather
            # NOTE: fxn only currently works when grouping along dim 0
            #       By swapping dimensions, should be possible to generalize
            assert dim == 0
            
            if len(x.shape) > 1:
                group_indices_rep = self.unsqueeze_vector_to_match(group_indices, x,
                                                               matching_dim = dim)
                repeat_params = list(x.shape)
                repeat_params[dim] = 1
                group_indices_rep = group_indices_rep.repeat(*repeat_params)
            else:
                group_indices_rep = group_indices
                
            
            # compute scattered softmax
            h_exp = torch.exp(h)
            h_exp_sum = segment_coo(h_exp, group_indices, reduce = "sum") 
            
            # make the dimensions match up with the original h_exp to get softmax vals
            h_exp_sum = torch.gather(h_exp_sum, dim = dim, 
                                     index = group_indices_rep)
            softmax_vals = h_exp/h_exp_sum
            
            # perform pooling
            pooled = segment_coo(x*softmax_vals, group_indices, reduce = "sum") 
            return pooled
        
    def unsqueeze_vector_to_match(self, vector, tensor, matching_dim):
        # say vector has size (3,) and tensor has size (5,3,6,1) and matching_dim = 1
        # returns a vector (technically now tensor) of size (1,3,1,1)
        vector = vector[(None,)*matching_dim]
        vector = vector[(...,) + (None,)*(len(tensor.shape)-matching_dim-1)]
        return vector
        

class EmbeddingPooledClassifier(torch.nn.Module):
    # This model performs a linear mapping on each embedded word in each subdocument
    # Then it performs softmax pooling over the word mappings within each subdocument
    # Then it performs softmax pooling over subdocument mappings for each document
    # At this point, we have a single value for each document, so this result is
    #       passed through the logistic fxn to make a prediction for each doc
    #
    # A temperature parameter is learned to tune the softmax pooling between
    #                                        average pooling and max pooling
    def __init__(self, embedding_size, n_labels = 1, temperature_init = 1):
        super().__init__()
        self.linear = torch.nn.Linear(in_features = embedding_size,
                                      out_features = n_labels)
        torch.nn.init.xavier_uniform_(self.linear.weight, gain = 0.01)
        
        self.pool_words = ParametricSoftmaxPool(temperature_init)
        self.pool_subdocs = ParametricSoftmaxPool(temperature_init)
    
    def forward(self, embeddings, subdoc_indices, attn_masks):
        # remove this squeeze once n_labels > 1 is implemented
        z = self.linear(embeddings).squeeze(2) 
        z_pool_words = self.pool_words(z, dim = 1, mask = attn_masks)
        z_pool_subdocs = self.pool_subdocs(z_pool_words, dim = 0, 
                                          group_indices = subdoc_indices)
        return z_pool_subdocs # unnormalized output (i.e. apply sigmoid later)
    

    def evaluate_AUROC(self, X, subdoc_lengths, attn_mask, y):
        self.eval()
        y_hat = torch.sigmoid(self.forward(X, subdoc_lengths, attn_mask).detach())
        performance = AUC(y_hat, y.long())
        self.train()
        return performance.item()
    

class LinearScheduler(object):
    # linearly updates learning rate from start value to stop value over 
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
                warnings.warn("Scheduler has already finished its last iteration.  No further learning rate changes will be made.")
                self.raised_warning = True


# regularization functions
l1_reg = lambda w: torch.abs(w).mean()
l2_reg = lambda w: torch.square(w).mean()