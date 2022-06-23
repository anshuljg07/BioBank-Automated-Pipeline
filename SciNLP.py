import os
import scispacy
import spacy
import pandas as pd
from spacy import displacy
from scispacy.abbreviation import AbbreviationDetector
from scispacy.linking import EntityLinker
from openpyxl import load_workbook


dfs = pd.read_excel('xlsxfiles/biobankrepo.xlsx', sheet_name='biobank scraped pdfs')

# print('data = {}'.format(dfs))
# print(type(dfs))
tempdf = dfs.iloc[[2]]  # pulls out the 2nd index or 3rd row
# print(tempdf.iloc[0, 3])  # pulls out the 3rd index or 4th column of the 3rd row
# text = tempdf.iloc[0, 3]
text = "specimens are prepared for electron microscopy and semi -thin sections stained with toluidine blue are reviewed prior to thin sectioning for ultrastructural examination . electron microscopy demonstrates patent capillary loops . the glomerular architecture demonstrates corrugation and thickening of basement membranes with no subepithelial deposits and no intramembranous deposits . the tubules show dilated mitochondria and injury . there is global effacement of foot processes . there are no subendothelial deposits . the mesangium shows an increase in matrix . mesangial electron dense deposits are not identified . "

# nlp_med = spacy.load('en_core_sci_md')  # download/load scispacy medical verbage library
nlp_large = spacy.load('en_core_sci_lg')
# nlp = spacy.load('en_ner_bionlp13cg_md')
# nlp_med.add_pipe("abbreviation_detector")
nlp_large.add_pipe("abbreviation_detector")
# doc_med = nlp_med(text)  # generate nlp processed doc
doc_large = nlp_large(text)

# print('Entered text = {}\n\n'.format(list(doc.sents)))
# print('Entries = {}'.format(doc.ents))


# GETS ABBREVIATIONS OUT OF TEXT
# for abrv in doc_med._.abbreviations:
#     print(f"{abrv} \t ({abrv.start}, {abrv.end}) {abrv._.long_form}")

# GETS ENTITIES OUT OF TEXT (pulling out verbs/adjectives out of EM)
# for ent in doc_large.ents:
#     print('"{}" has label {}'.format(ent.text, ent.label_))

# GETS TOKENS OUT OF TEXT
for token in doc_large:
    print('token = {}\t\t head = {}\t\t children = {}'.format(
        token.text, token.head.text, list(token.children)))

for ent in doc_large.ents:
    print('"{}" head = {} children'.format(ent.text, ent.head))


# DISPLAY ENTITIES USING DISPLACY
# displacy.serve(doc_large, style="ent")


# for chunk in doc_med.noun_chunks:
#     print('text = "{}"\t\troot = {}\t\tdep = {}'.format(
#         chunk.text, chunk.root.text, chunk.root.dep_))
# for chunk in doc_large.noun_chunks:
#     print('text = "{}"\t\troot = {}\t\tdep = {}'.format(
#         chunk.text, chunk.root.text, chunk.root.dep_))


# display sentence structure/relations in webpage
# displacy.serve(doc, style='dep')

# homepath = '/Users/anshulgowda/Documents/CODE/KUH2022/xlsfiles'
# processedpath = '/Users/anshulgowda/Documents/CODE/KUH2022/xlsxfiles'
# # for doc in os.listdir(os.getcwd()):
# for doc in os.listdir('/Users/anshulgowda/Documents/CODE/KUH2022/xlsxfiles'):
#     print(doc)
#     os.rename('{}/{}'.format(processedpath, doc, ), '{}/{}'.format(processedpath, doc))
