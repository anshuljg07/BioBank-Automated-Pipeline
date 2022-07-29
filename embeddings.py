import torch
from simpletransformers.language_representation import RepresentationModel
import pandas as pd
import openpyxl

if torch.cuda.is_available():
    device = torch.device('cuda')
    print('There are %d GPU(s) available.' % torch.cuda.device_count())
    print('We will use the GPU:', torch.cuda.get_device_name(0))
    usingCUDA = True
else:
    print('No GPU available, using the CPU instead.')
    usingCUDA = False

clinicalsentence = "findings most consistent with lupus nephritis , rps class ii , with chronicity. striped fibrosis and nodular hyalinosis in arterioles , consistent with chronic calcineurin inhibitory toxicity - acute tubular injury. acute tubular injury with findings suspicious for bile cast nephropathy. severe , diffuse acute tubular injury - patchy acute interstitial nephritis."
sentences = clinicalsentence.split('.')

nonclinicalmodel = RepresentationModel(
    model_type='bert',
    model_name='bert-base-uncased',
    use_cuda=usingCUDA  # if using google collab's GPUs, set this equal to True
)

clinicalmodel = RepresentationModel(
    model_type='bert',
    model_name='emilyalsentzer/Bio_ClinicalBERT',
    use_cuda=usingCUDA  # if using google collab's GPU, set this equal to True
)
nonclinical_sentence_vectors = clinicalmodel.encode_sentences(sentences, combine_strategy='mean')
clinical_sentence_vectors = clinicalmodel.encode_sentences(sentences, combine_strategy='mean')
print(clinical_sentence_vectors)
print(type(clinical_sentence_vectors))

#df = pd.read_excel('xlsxfiles/AINBankrepo.xlsx')
df = pd.read_excel('/Users/anshulgowda/Documents/CODE/KUH2022/xlsxfiles/AINBankrepo.xlsx')
#print(df)

#print(df.iloc[2, 1:7])
