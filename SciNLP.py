import os
import scispacy
import spacy
import pandas as pd
from spacy import displacy
from scispacy.abbreviation import AbbreviationDetector
from scispacy.linking import EntityLinker
from negspacy.negation import Negex
from openpyxl import load_workbook
from itertools import chain, combinations, permutations


'''
Object to represent the matches in a document. Attributes include the unique CUI, entity.text, Canonical name, USML definition,
and the dependency information, which includes the head and children of the given tokens
'''


class Group:
    def __init__(self, cui, entity, canon, definition, family):
        self.cui = cui
        self.entity = entity
        self.canon = canon
        self.definition = definition
        self.family = family

    '''
    Use Negspacy to see if the individual tokens are negated or carry a negation token.
    '''

    def find_negation(self):
        pass


'''
Object that corresponds to a Named Entity using the Spacy Named Entity Recognizer (NER). The named entity is generated
using Spacy's NLP algorithim trained on clinical data. This entity is then searched for in the USML (KB || Knowledge Base),
and returns a named entity match if it exists. This named entity match gets a unique ID (CUI) and is given a clinical umbrella
term (canon || canonical name), and if it exists an associated medical definition. If matches are not found the named entity is
checked for gramatical dependency tokens, which are stored in family. Using Negspacy, an algorithim that detects for negation,
negation is noted with relation to the named entity.
'''


class CUIgroup(Group):
    # def __init__(self, cui, canon, definition, family, negation):
    def __init__(self, cui, entity, canon, definition, family, negation):
        super().__init__(cui, entity, canon, definition, family)
        self.subCUIgroups = []  # store the subCUIgroup objects
        self.subCUIs = []  # store the CUIs (vals)
        self.containSubs = False

        # self.cui = cui
        # self.entity = entity
        # self.canon = canon
        # self.definition = definition
        # self.family = family
        # self.subcuiexists = False  # contains a list of the head/children for each token in the entity
        # contain a dictionary of inner CUIs and their matching text query
        # hello
        # self.head = head
        # self.children = children
        # self.negation = negation #to be added soon once how to do negation is figured out

    def addsubCUI(self, subCUI, subCUIgroup):
        if(not self.containSubs):
            self.containSubs = True
        self.subCUIs.append(subCUI)
        self.subCUIgroups.append(subCUIgroup)

    def find_negation(self):  # keep in parent class? or keep in the children?
        pass


'''
Object meant to be the subCUIs inside of the larger CUIgroup, multiple subCUIs may exist for a CUIgroup that resulted
in no matches in the KB. Therefore a NULL valued CUIgroup may have multiple non-NULL-valued subCUI groups
'''


class subCUIgroup(Group):
    # should I store the text, the entity, or the token?
    def __init__(self, cui, entity, canon, definition, family):
        super().__init__(cui, entity, canon, definition, family)


'''
Object meant to hold the text of an individual section dervied from the ScrapeDriver. Contains an Analyze() function to
use the Spacy's Named Entity Recognizer (NER), which uses a machine learned model trained on clinical data to recognize
common clinical entities. These are then cross referenced with the USML {word for collection of words}, and matches are found.
'''


class Section:
    def __init__(self, text):
        self.fmt_str = "{:<20} | {:<10} | {:<20} | {:<40}"
        self.sub_fmt_str = "\t{:<15} ~ {:<15} ~ {:<35}"
        self.query_fmt = "{:<20} $ {:<20} $ {:<20}"
        self.donerecursion = False
        self.text = text
        self.cuis = []
        self.cuigroups = []

        # testing viability
        self.tempNullValCUI = None

    def __repr__(self):
        print(self.fmt_str.format("Entity", "1st CUI", "Canonical Name", "Definition"))
        for group in cuigroups:
            if(not group.subcuiexists):  # if no subcuis exists
                print(fmt_str.format(group.entity.text, group.cui, group.canon, group.definition))
            else:
                # print out the subcui entities

    def Analyze(self, nlp, linker):
        doc = nlp(self.text)
        for entity in doc.ents:
            self.donerecursion = False
            self.tempNullValCUI = None
            CUIsearch_helper(entity, nlp, linker)
            self.cuigroups.append(self.tempNullValCUI)

    # add variable for recursion ('recurs')
    # make linker a class attribute??
    def CUIsearch_helper(self, entity, nlp, linker):
        if(len(entity._.kb_ents) != 0):  # match exists in kb
            first_cuid = entity._.kb_ents[0][0]  # CAN I REPLACE "CUID" with "CUI"
            query = linker.kb.cui_to_entity[first_cuid]  # CAN I REPLACE "CUID" with "CUI"

            # if first match's CUID doesn't return a definition, keep looking for a match that has a def.
            # do i need to try and find a match that has a definition or is a CUI enough
            if(None == query.definition):
                for i, kb_entry in enumerate(entity._.kb_ents):
                    if i == 0:
                        continue
                    cuid = kb_entry[0]  # can "cuid" be replaced with "cui"?
                    query = linker.kb.cui_to_entity[first_cuid]

                    if(None == query.definition):
                        cui = kb_entry[0]
                        match_score = kb_entry[1]
                        continue
                    else:  # found a match with a Definition
                        # no match was found originally, so create null valued CUI group (None for family). Then link it to
                        # the null valued CUIgroup
                        if(self.donerecursion and self.tempNullValCUI != None):
                            subgroup = subCUIgroup(
                                cui, entity, query.canonical_name, query.definition, None)

                            # link to the null valued CUI group
                            self.tempNullValCUI.subCUIgroups.append(subgroup)
                            self.tempNullValCUI.subCUIs.append(cui)
                            self.cuis.append(cui)
                            return
                        else:
                            family = find_HeadandChildren(entity.text, nlp)
                            tempCUI = CUIgroup(cui, entity, query.canonical_name,
                                               query.definition, family)
                            self.cuigroups.append(tempCUI)  # add cui grouping to the list of groups
                            self.cuis.append(cui)  # add unique cui to the list of cuis
                            print(self.fmt_str.format(entity.text, cui,
                                                      query.canonical_name, query.definition))
                            return

                # if for loop completes then no match with a definition was found, so use the first match (best match)
                if(self.donerecursion and self.tempNullValCUI != None):
                    subgroup = subCUIgroup(first_cuid, entity, query.canonical_name, '', None)

                    # link to the null valued CUI group
                    self.tempNullValCUI.subCUIgroups.append(subgroup)
                    self.tempNullValCUI.subCUIs.append(first_cuid)
                    self.cuis.append(first_cuid)
                    return
                else:
                    family = find_HeadandChildren(entity.text, nlp)
                    tempCUI = CUIgroup(first_cuid, entity, query.canonical_name, '', family)
                    self.cuigroups.append(tempCUI)
                    self.cuis.append(first_cuid)
                    print(self.fmt_str.format(entity.text, first_cuid, query.canonical_name, ''))
                    return

            # if the first match contains a definition use the first match
            else:
                if(self.donerecursion and self.tempNullValCUI != None):
                    subgroup = subCUIgroup(
                        first_cuid, entity, query.canonical_name, query.definition, None)

                    # link to the null valued CUI group
                    self.tempNullValCUI.subCUIgroups.append(subgroup)
                    self.tempNullValCUI.subCUIs.append(first_cuid)
                    self.cuis.append(first_cuid)
                    return

                else:
                    family = find_HeadandChildren(entity.text, nlp)
                    # since no def exists, pass empty string
                    # possible that .canonical_name could return NoneType as well
                    tempCUI = CUIgroup(first_cuid, entity, query.canonical_name,
                                       query.definition, family)
                    self.cuigroups.append(tempCUI)
                    self.cuis.append(first_cuid)

        else:  # match doesn't exist in kb
            if(self.donerecursion == True):
                return
            # family = find_HeadandChildren(entity.text, nlp)
            # noCUI = CUIgroup(None, entity, None, None, family) #create a null valued CUIgroup
            # self.cuigroups.append(noCUI)

            # CHECKING VIABILITY
            family = find_HeadandChildren(entity.text, nlp)
            self.tempNullValCUI = CUIgroup(None, entity, None, None, family)
            self.tempNullValCUI.subcuiexists = True

            # add NullValCUI at the end or at the beginning? BEGNINNING OPTION
            # self.cuigroups.append(self.tempNullValCUI)

            # use the Spacy tokenizer to analyze dependencies
            if(len(family > 0)):
                subtext = entity.text
                sub_doc = nlp(subtext)
                heads = []            # contain the heads of the text
                children = []         # contain the children of the text
                head_combos = []      # contain all possible combinations/permutations of the heads
                child_combos = []     # contain all possible combinations/permutations of the children

                for token in sub_doc:
                    if(len(list(token.children)) != 0):  # if the token contains children, then the token is a head
                        if(token.head.text not in heads):
                            heads.append(token.head.text)

                            # add the children to the children list, if they do not already exist, non list comp. version below
                            [children.append(i.text)
                             for i in list(token.children) if i.text not in children]
                            # for i in list(token.children):
                            #     children.append(i.text) #add the head's children to the

                # generates all possible combinations of heads from size (0 -> n)
                head_combos = list(chain.from_iterable(permutations(heads, r)
                                                       for r in range(len(heads)+1)))

                # generates a powerset of all possible combinations of heads for those of size (1 -> n-1)
                # head_combos = list(chain.from_iterable(combinations(heads, r) for r in range(len(heads)+1)))

                # generates all possible combinations of children from size (0 -> n)
                child_combos = list(chain.from_iterable(permutations(children, r)
                                                        for r in range(len(children)+1)))
                # generates a powerset of all possible combinations of heads for those of size (1 -> n-1)
                # child_combos = list(chain.from_iterable(combinations(children, r) for r in range(len(children)+1)))

                head_combos = list(head_combos)
                child_combos = list(child_combos)

                print(head_combos)
                print(child_combos)

                for i, headcombo in enumerate(head_combos):
                    if(len(headcombo) == 0):
                        continue
                    for j, childrencombo in enumerate(child_combos):
                        if(len(childrencombo) == 0):
                            continue
                    # generate subquery string, that will be fed to the KB
                    subquery = (' '.join(childrencombo)) + ' ' + (' '.join(headcombo))
                    print(query_fmt.format(' '.join(childrencombo), ' '.join(headcombo), subquery))

                    # if you're simply searching for the original entity, skip it
                    if subquery == entity.text:
                        continue

                    # run entity recognizer on the subquery
                    innerdoc = nlp(subquery)
                    for innerentity in innerdoc.ents:
                        # handle recursion
                        self.donerecursion = True
                        CUIsearch_helper(self, innerentity, nlp, linker)

            # print(fmt_str.format(entity.text, 'xxxxxxxx', 'NO ENTRY FOUND', 'NO DEF'))

            # find combinations of the head + children and search for them in the KB.
            # takes the subtext and finds the head/children of them and returns them to be loaded into the CUIgroup's head and
            # children attributes

    '''
    given a subtext, and the nlp algo to interpret it. The
    '''

    def find_HeadandChildren(self, subtext, nlp):
        if(subtext.split() > 1):
            familycollection = []
            sub_doc = nlp(subtext)
            for token in sub_doc:
                familycollection.append([token.text, token.head.text, list(token.children)])
            return familycollection
        else:
            return []


class NLPDriver():
    def __init__(self):
        # try and get the pip installation for the lg file (TIMES OUT, BAD WIFI?)
        self.nlp = spacy.load("en_core_sci_md")
        self.nlp.add_pipe("scispacy_linker", config={
            "resolve_abbreviations": True, "linker_name": "umls"})
        self.linker = nlp.get_pipe("scispacy_linker")


def CUIsearch(entity, nlp, fmt_str, recurs):
    # check if matches exist in the knowledge base
    if(len(entity._.kb_ents) != 0):
        # take the first match (coincidentally the highest match score)
        first_cuid = entity._.kb_ents[0][0]
        query = linker.kb.cui_to_entity[first_cuid]
        # if(None in [query.canonical_name, query.definition]):
        if(None == query.definition):
            for i, kb_entry in enumerate(entity._.kb_ents):
                if i == 0:
                    continue
                cuid = kb_entry[0]
                query = linker.kb.cui_to_entity[first_cuid]
                # if(None in [query.canonical_name, query.definition]):
                if(None == query.definition):
                    tempfmt = "{:<15} | {:<20} | {:<11} | {:<6} | {:<5} | {:<5}"
                    cui = kb_entry[0]
                    match_score = kb_entry[1]
                    print(tempfmt.format('NOT FOUND', entity.text, cui, match_score,
                                         str(None != query.canonical_name), str(None != query.definition)))
                    continue
                else:
                    print(fmt_str.format(entity.text, first_cuid,
                                         query.canonical_name, query.definition[0:40] + "..."))
                    return
            print(fmt_str.format(entity.text, cui, 'ENTRIES FOUND', 'NO DEF'))
        else:
            print(fmt_str.format(entity.text, first_cuid,
                                 query.canonical_name, query.definition[0:40] + "..."))
            if(len(entity.text.split()) > 1):
                subtext = entity.text
                sub_doc = nlp(subtext)
                sub_fmt_str = "\t{:<15} ~ {:<5} ~ {:<15} ~ {:<35}"
                for token in sub_doc:
                    print(sub_fmt_str.format(token.text, str(len(entity.text.split())), token.head.text,
                                             '{}'.format(list(token.children))))

    else:  # no match found in kb, so no CUI/match confidence tuples in kb_ents
        if(recurs == True):
            return
        print(fmt_str.format(entity.text, 'xxxxxxxx', 'NO ENTRY FOUND', 'NO DEF'))
        subtext = entity.text
        sub_doc = nlp(subtext)
        sub_fmt_str = "\t{:<15} ~ {:<15} ~ {:<35}"
        heads = []
        children = []
        head_combos = []
        child_combos = []

        for token in sub_doc:
            if(len(list(token.children)) != 0):  # if the token contains children, then the token is a head
                # add the .head object (to get the text, use .head.text)
                heads.append(token.head.text)
                for i in list(token.children):
                    children.append(i.text)

        # once all the heads and tokens are fxound, use the algo
        # for r in range(len(heads)+1):
        #     if(len(chain.from_iterable(combinations(heads, r))) == len(heads)):
        #         head_combos.append(chain.from_iterable(combinations(heads, r)))
        # for r in range(len(s)+1):
        #     if(len(chain.from_iterable(combinations(s, r))) == len(s)):
        #         output.append(chain.from_iterable(combinations(s, r)))

        # generates all possible combinations of heads from size (0 -> n)
        head_combos = list(chain.from_iterable(permutations(heads, r) for r in range(len(heads)+1)))

        # generates a powerset of all possible combinations of heads for those of size (1 -> n-1)
        # head_combos = list(chain.from_iterable(combinations(heads, r) for r in range(len(heads)+1)))

        # generates all possible combinations of children from size (0 -> n)
        child_combos = list(chain.from_iterable(permutations(children, r)
                                                for r in range(len(children)+1)))
        # generates a powerset of all possible combinations of heads for those of size (1 -> n-1)
        # child_combos = list(chain.from_iterable(combinations(children, r) for r in range(len(children)+1)))
        head_combos = list(head_combos)
        child_combos = list(child_combos)

        print(head_combos)
        print(child_combos)

        # messing with the terminal, commands
        # output=list(chain.from_iterable(permutations(s, r) for r in range(len(s)+1)))
        # output2=list(chain.from_iterable(combinations(s, r) for r in range(len(s)+1)))

        # algorithim for searching all of the head combos + children combos
        query_fmt = "{:<20} $ {:<20} $ {:<20}"
        for i, headcombo in enumerate(head_combos):
            if(len(headcombo) == 0):
                continue
            for j, childrencombo in enumerate(child_combos):
                if(len(childrencombo) == 0):
                    continue
                # combine the children and head combo into a queriable string
                # headquery = ' '.join(headcombo)
                # print('childrencombo: ')
                # print(childrencombo)
                # childrenquery = ' '.join(childrencombo)
                # subqeury = childrenquery + ' ' + headquery
                subquery = (' '.join(childrencombo)) + ' ' + (' '.join(headcombo))
                print(query_fmt.format(' '.join(childrencombo), ' '.join(headcombo), subquery))

                # if you're simply searching for the original entity, skip it
                if subquery == entity.text:
                    continue

                # run entity recognizer on the subquery
                innerdoc = nlp(subquery)
                for innerentity in innerdoc.ents:
                    recurs = True
                    CUIsearch(innerentity, nlp, fmt_str, recurs)
                # do I create a new subCUI function, or use the old CUIsearch function

    # prints all of the tokens and their dependenices for entities with no match in the KB
        for token in sub_doc:
            print(sub_fmt_str.format(
                token.text, token.head.text, '{}'.format(list(token.children))))

# iteration 1, before I understood how what kb_ents was


def CUIsearch_temp(entity, nlp):
    try:
        first_cuid = entity._.kb_ents[0][0]
        kb_entry = linker.kb.cui_to_entity[first_cuid]
        if(None in [kb_entry.canonical_name, kb_entry.definition]):
            print(fmt_str.format(entity.text, 'xxxxxxxx', 'NO ENTRY FOUND', 'NO DEF'))
            subtext = entity.text
            sub_doc = nlp(subtext)
            sub_fmt_str = "\t{:<15} ~ {:<15} ~ {:<35}"
            for token in sub_doc:
                print(sub_fmt_str.format(
                    token.text, token.head.text, '{}'.format(list(token.children))))
        else:

            print(fmt_str.format(entity.text, first_cuid,
                                 kb_entry.canonical_name, kb_entry.definition[0:40] + "..."))

    except IndexError:
        kb_entry = None
        print(fmt_str.format(entity.text, 'CUI INDERROR', 'NO ENTRY FOUND', 'NO DEF'))


dfs = pd.read_excel('xlsxfiles/biobankrepo.xlsx', sheet_name='biobank scraped pdfs')

# print('data = {}'.format(dfs))
# print(type(dfs))
tempdf = dfs.iloc[[2]]  # pulls out the 2nd index or 3rd row
# print(tempdf.iloc[0, 3])  # pulls out the 3rd index or 4th column of the 3rd row
# text = tempdf.iloc[0, 3]
# text = "specimens are prepared for electron microscopy and semi -thin sections stained with toluidine blue are reviewed prior to thin sectioning for ultrastructural examination . electron microscopy demonstrates patent capillary loops . the glomerular architecture demonstrates corrugation and thickening of basement membranes with no subepithelial deposits and no intramembranous deposits . the tubules show dilated mitochondria and injury . there is global effacement of foot processes . there are no subendothelial deposits . the mesangium shows an increase in matrix . mesangial electron dense deposits are not identified . "

word_bank = [['ifta', 'interstitial fibrosis tubular atrophy'], ['if/ta', 'interstitial fibrosis/tubular atrophy'], 'interstitial fibrosis/tubular atrophy', 'interstital fibrosis', 'tubular atrophy', 'fibrosis', 'tubular injury', 'tubulitis', 'infiltrate', 'crescents', ['ain', 'acute interstitial nephritis'],
             ['acute interstitial nephritis'], ['cin', 'contrast-induced nephropathy'], 'glomeruli', 'global glomerulosclerosis', 'segmental glomerulosclerosis', 'interstitial infiltrate', 'eosinophils', 'acute tubular injury', 'cores-michels', 'cores-zeus', 'arteriosclerosis', 'mesangial expansion', 'mesangial hypercellularity', 'cores-light']

# text = 'SBMA Rick has fibrosis, IFTA, IF, TA. There is extrememe interstital fibrosis and tubular atrophy with little fibrosis. Sarah has tubular injury with moderate infiltrate and wide crescents.'
text = 'aki with possible vanco toxicity -atn versus ain '

# nlp_sm = spacy.load('en_core_sci_sm')  # download/load scispacy medical verbage library
# nlp_sm.add_pipe("scispacy_linker", config={"linker_name": "umls", "max_entities_per_mention": 3})
# linker = nlp_sm.get_pipe("scispacy_linker")
# nlp_large = spacy.load('en_core_sci_lg')
# nlp = spacy.load('en_ner_bionlp13cg_md')
# nlp_large.add_pipe("abbreviation_detector")
# nlp_large.add_pipe("abbreviation_detector")
# doc_sm = nlp_sm(text)  # generate nlp processed doc
# doc_large = nlp_large(text)

# print('Entered text = {}\n\n'.format(list(doc.sents)))
# print('Entries = {}'.format(doc.ents))


# GETS ABBREVIATIONS OUT OF TEXT
# print(f"{abrv} \t ({abrv.start}, {abrv.end}) {abrv._.long_form}")

# GETS ENTITIES OUT OF TEXT (pulling out verbs/adjectives out of EM)
# for ent in doc_large.ents:
#     print('"{}" has label {}'.format(ent.text, ent.label_))

# GETS TOKENS OUT OF TEXT
# for token in doc_sm:
#     print('token = {}\t\t head = {}\t\t children = {}'.format(
#         token.text, token.head.text, list(token.children)))

# GET ENTITIES OUT OF TEXT
# for ent in doc_med.ents:
#     print('entity = "{}"'.format(ent.text))

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

# Add the abbreviation pipe to the spacy pipeline.
# nlp_sm.add_pipe("abbreviation_detector")
# doc = nlp_sm("(CLL), autoimmune hemolytic anemia, and oral ulcer. The patient was diagnosed with chronic lymphocytic leukemia and was noted to have autoimmune hemolytic anemia at the time of his CLL diagnosis.")
# fmt_str = "{:<6}| {:<30}| {:<6}| {:<6}"
# print(fmt_str.format("Short", "Long", "Starts", "Ends"))
# for abrv in doc._.abbreviations:
#     print(fmt_str.format(abrv.text, str(abrv._.long_form), abrv.start, abrv.end))

# Entity Linker
# fmt_str = "{:<20}| {:<10}| {:<32}| {:<20}"
# print(fmt_str.format("Entity", "1st CUI", "Canonical Name", "Definition"))
# for entity in doc_sm.ents:
#     first_cuid = entity._.kb_ents[0][0]
#     kb_entry = linker.kb.cui_to_entity[first_cuid]
#     print(fmt_str.format(entity.text, first_cuid,
#                          kb_entry.canonical_name, kb_entry.definition[0:15] + "..."))

# nlp = spacy.load("en_core_sci_sm")
nlp = spacy.load("en_core_sci_md")
nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "linker_name": "umls"})
linker = nlp.get_pipe("scispacy_linker")
# doc = nlp(" worsening renal insufficiency since 1 /2021, history of systemic therapy for metastatic pancreatic cancer. kidney , biopsy : - focal and segmental glomerulosclerosis , favor primary - diffuse acute tubular injury. - severe arterionephrosclerosis - acute tubular injury")
# doc = nlp(" 30 -year-old woman with persistent hematuria and preserved gfr . evaluate for tbm versus other occult cause for hematuria . also interested to see if any areas of focal ischemic damage consistent with vasospasm as she has been diagnosed with loin pain hematuria")
doc = nlp(" the biopsy consists of one fragment which is stained with h &e, pas , trichrome , jones silver and hps stains . review of all stains reveals at least 10 glomeruli of which three are globally sclerosed . the architecture of the kidney is relatively well -preserved. there is mild interstitial fibrosis and tubular atrophy (~5%). there is a patchy interstitial monomorphic small lymphocytic infiltrate involving ~5-10% of the biopsy tissue . the tubules show acute tubular injury . immunohistochemistry shows that the infiltrating lymphocytes are cd20 variably positive b -cells, which co -express cd5 . cd3 highlights admixed t cells . congo red stain is positive for focal congophilic deposits in arterioles and the glomerular mesangium . intimal sclerosis is present . ")
# linker = nlp.get_pipe("scispacy_linker")

fmt_str = "{:<20} | {:<10} | {:<20} | {:<40}"
print(fmt_str.format("Entity", "1st CUI", "Canonical Name", "Definition"))
donerecursion = False

for entity in doc.ents:
    CUIsearch(entity, nlp, fmt_str, donerecursion)
    # temp = 'segmental glomerulosclerosis'
    # tempfmt = "{:<20}| {:<11}| {:<6}"
    # if(entity.text == temp.lower()):
    # CUIsearch(entity, nlp, fmt_str)
    #     for kb_entry in entity._.kb_ents:
    #         cui = kb_entry[0]
    #         match_score = kb_entry[1]
    #         print(tempfmt.format(entity.text, cui, match_score))
    # try:
    #     fmt_str = "{:<20}| {:<5}| {:<20}"
    # # print(type(entity.text), type(str(len(entity._.kb_ents))), type(entity._.kb_ents[0]))
    #     print(fmt_str.format(entity.text, str(len(entity._.kb_ents)),
    #                          '{}'.format(entity._.kb_ents[0])))
    # except IndexError:
    #     fmt_str = "{:<20}| {:<5}"
    #     print(fmt_str.format(entity.text, str(len(entity._.kb_ents))), end=" | ")
    #     print(entity._.kb_ents)

    # for kb_entry in entity._.kb_ents:
    #     cui = kb_entry[0]
    #     match_score = kb_entry[1]
    #     print(fmt_str.format(entity.text, cui, match_score))

    # try:  # WEIRD error where ATI is repeated, but a CUI is only generated for the repeat instance
    #     first_cuid = entity._.kb_ents[0][0]
    #     kb_entry = linker.kb.cui_to_entity[first_cuid]
    # except IndexError:
    #     print(fmt_str.format(entity.text, 'CUI INDERROR', 'NO ENTRY FOUND', 'NO DEF'))
    # # CUI generated but not found in db, examine word parts inside?
    # if(None in [kb_entry.canonical_name, kb_entry.definition]):
    #     print(fmt_str.format(entity.text, 'xxxxxxxx', 'NO ENTRY FOUND', 'NO DEF'))
    #
    #     # further resolves entities without a match, by analyzing dependencies, possibly redo CUI search on the HEAD
    #     # if the HEAD is not the same as the entity (insinuating actual dependency)
    #     subtext = entity.text
    #     sub_doc = nlp(subtext)
    #     sub_fmt_str = "\t{:<15} ~ {:<15} ~ {:<35}"
    #     for token in sub_doc:
    #         print(sub_fmt_str.format(
    #             token.text, token.head.text, '{}'.format(list(token.children))))
    # else:
    #     print(fmt_str.format(entity.text, first_cuid,
    #                          kb_entry.canonical_name, kb_entry.definition[0:40] + "..."))

# entity = doc.ents[1]
# for umls_ent in entity._.kb_ents:
#     print(linker.kb.cui_to_entity[umls_ent[0]])
