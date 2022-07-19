import spacy
import scispacy
from spacy import displacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span
from negspacy.negation import Negex
from negspacy.termsets import termset


class Negatizer:
    def __init__(self, text):
        self.nlp0 = spacy.load("en_core_sci_sm")
        self.nlp1 = spacy.load("en_ner_bc5cdr_md")
        self.clinical_note = text
        self.lemmatized = None
        self.nlp_model = "en_ner_bc5cdr_md"
        self.neg_nlp = None

    def lemmatize(self):
        doc = self.nlp1(self.clinical_note)
        lemNote = [wd.lemma_ for wd in doc]
        self.lemmatized = " ".join(lemNote)

    def neg_model(self):
        nlp = spacy.load(self.nlp_model, disable=['parser'])
        nlp.add_pipe('sentencizer')
        # negex = Negex(nlp)
        ts = termset('en_clinical_sensitive')
        nlp.add_pipe("negex", config={"neg_termset": ts.get_patterns(),
                                      "chunk_prefix": ["no"], }, last=True,)

        # nlp.add_pipe(negex)
        self.neg_nlp = nlp

    def negation_handling(self):
        results = []
        self.neg_model()
        splittext = self.clinical_note.split(".")
        splittext = [n.strip() for n in splittext]

        for t in splittext:
            doc = self.neg_nlp(t)
            for e in doc.ents:
                rs = str(e._.negex)
                if(rs == "True"):
                    results.append(e.text)
        return results


def main():
    # text = "Patient resting in bed. Patient given azithromycin without any difficulty. Patient has audible wheezing, \
    # states chest tightness. No evidence of hypertension.\
    # Patient denies nausea at this time. zofran declined. Patient is also having intermittent sweating associated with pneumonia. \
    # Patient refused pain but tylenol still given. Neither substance abuse nor alcohol use however cocaine once used in the last year. Alcoholism unlikely.\
    # Patient has headache and fever. Patient is not diabetic. \
    # No signs of diarrhea. Lab reports confirm lymphocytopenia. Cardaic rhythm is Sinus bradycardia. \
    # Patient also has a history of cardiac injury. No kidney injury reported. No abnormal rashes or ulcers. \
    # Patient might not have liver disease. Confirmed absence of hemoptysis. Although patient has severe pneumonia and fever \
    # , test reports are negative for COVID-19 infection. COVID-19 viral infection absent."
    text = "the biopsy consists of one fragment which is stained with h &e, pas , trichrome , jones silver and hps stains . review of all stains reveals at least 10 glomeruli of which three are globally sclerosed . the architecture of the kidney is relatively well -preserved. there is mild interstitial fibrosis and tubular atrophy (~5%). there is a patchy interstitial monomorphic small lymphocytic infiltrate involving ~5-10% of the biopsy tissue . the tubules show acute tubular injury . immunohistochemistry shows that the infiltrating lymphocytes are cd20 variably positive b -cells, which co -express cd5 . cd3 highlights admixed t cells . congo red stain is positive for focal congophilic deposits in arterioles and the glomerular mesangium . intimal sclerosis is present . "
    Neg = Negatizer(text)
    Neg.lemmatize()
    # print(Neg.lemmatized)
    print(Neg.negation_handling())


main()
