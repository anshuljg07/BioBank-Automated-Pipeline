# -*- coding: utf-8 -*-
"""
Created on Wed Jul 27 23:58:12 2022

@author: adityabiswas
"""

import pandas as pd

###############################################################################
##### Preprocess Clinical Note

# load  clinical note
df_clinical_note = pd.read_excel("H:/Data/NLP Clinical Text Analysis/Dennis Project/AINBankrepo.xlsx")
df_clinical_note.fillna('', inplace = True)

# concatenate separate notes into single string
text = df_clinical_note[['lm_results', 'em_results']].agg(''.join, axis = 1)
text.index = df_clinical_note['sequenceno']
text.name = 'text'

# remove rows with no data
keep = text.str.strip() != ''
text = text[keep]


###############################################################################
##### Preprocess Labels

# try crescents_seen next for a simpler target

# load all labels and change index to match clinical note
label_target = 'focal_glomerulosclerosis'
df_labels = pd.read_csv("H:/Data/NLP Clinical Text Analysis/Dennis Project/biopsy-abstracted-data.csv")
labels = df_labels[label_target]
labels.index = df_labels['sequenceno'].str.slice(start = 4)
labels.name = 'labels'

# subset to collected data and then transform label to binary
labels = labels[~labels.isna()]
labels[labels == -99] = 0
labels[labels > 0] = 1
labels = labels.astype(int)


###############################################################################
##### Join Note with Label and save

df = pd.concat([text, labels], axis = 1)
missing_text_select = df['text'].isna()
missing_labels_select = df['labels'].isna()
print("Clinical Note Missing: \n", list(df.index[missing_text_select].values))
print(label_target, "label Missing: \n", list(df.index[missing_labels_select].values))
keep = ~(missing_text_select | missing_labels_select)
df = df[keep]


df.to_csv("H:/Data/NLP Clinical Text Analysis/Dennis Project/data_cleaned.csv")

