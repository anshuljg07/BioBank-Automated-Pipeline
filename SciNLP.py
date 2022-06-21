import os
import scispacy
import spacy
import pandas as pd
from spacy import displacy
from scispacy.abbreviation import AbbreviationDetector

dfs = pd.read_excel('xlsxfiles/biobankrepo.xlsx', sheet_name='biobank scraped pdfs')

# print('data = {}'.format(dfs))
# print(type(dfs))
tempdf = dfs.iloc[[2]]  # pulls out the 2nd index or 3rd row
# print(tempdf.iloc[0, 3])  # pulls out the 3rd index or 4th column of the 3rd row
text = tempdf.iloc[0, 3]

# nlp = spacy.load('en_core_sci_md')  # download/load scispacy medical verbage library
# nlp.add_pipe("abbreviation_detector")
# doc = nlp(text)  # generate nlp processed doc

# print('Entered text = {}\n\n'.format(list(doc.sents)))
# print('Entries = {}'.format(doc.ents))

# for abrv in doc._.abbreviations:
# print(f"{abrv} \t ({abrv.start}, {abrv.end}) {abrv._.long_form}")


# display sentence structure/relations in webpage
# displacy.serve(doc, style='dep')

homepath = '/Users/anshulgowda/Documents/CODE/KUH2022/xlsfiles'
processedpath = '/Users/anshulgowda/Documents/CODE/KUH2022/xlsxfiles'
# for doc in os.listdir(os.getcwd()):
for doc in os.listdir('/Users/anshulgowda/Documents/CODE/KUH2022/xlsxfiles'):
    print(doc)
    os.rename('{}/{}'.format(processedpath, doc, ), '{}/{}'.format(processedpath, doc))
