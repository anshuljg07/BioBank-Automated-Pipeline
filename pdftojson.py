
# merch, pdfminer3 is now succesfully imported
import pdfminer3
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage  # gets the pages of a pdf
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter
import io  # wtf is io


resourcemanager = PDFResourceManager()
file_handler = io.BytesIO
converter = TextConverter(resourcemanager, file_handler, laparams=LAParams())
page_interpreter = PDFPageInterpreter(resourcemanager, converter)

with open('template_biopsy.pdf', 'rb') as fh:
    for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
        page_interpreter.process_page(page)

    text = file_handler.getvalue()

converter.close()
file_handler.close()
print(text)
