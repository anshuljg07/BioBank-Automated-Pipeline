# from PIL import *
from pdf2image import convert_from_path
import cv2
import pytesseract
from pytesseract import Output
import os
import re


def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def viewwithboxes(image, num, total):
    num += 1
    if(num == 1):
        print('\t\t\t~ DISPLAYING {} PAGE REPORT ~\n'.format(total))
    print('\t\t\t    Showing image {} of {}\n'.format(num, total))
    cv2.imshow('\t\t\t biopsy_with_boxes{}\n'.format(num), image)
    cv2.waitKey(4000)
    cv2.destroyAllWindows()


# def tiff_to_textboxfiles(i, j, pageinfodict, img, numpages, userviewinput):
def tiff_to_textboxfiles(i, j, pageinfodict, img, numpages):
    # def tiff_to_textboxfiles(i, j, numpages, userviewinput):
    # img = cv2.imread('TIFFS/Doc{}/Doc{}page{}.tiff'.format(str(i), str(i), str(j)))
    # pageinfodict = pytesseract.image_to_data(img, output_type=Output.DICT)
    # creation of boxes
    n_boxes = len(pageinfodict['text'])
    for k in range(n_boxes):
        if int(float(pageinfodict['conf'][k])) > 60:
            (x, y, w, h) = (pageinfodict['left'][k], pageinfodict['top']
                            [k], pageinfodict['width'][k], pageinfodict['height'][k])
            img = cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    # if not userviewinput:
    #     userviewinput = input('View text identified version of .tiff files? (Y/N)')
    # if(userviewinput in ['Y', 'yes', 'y', 'YES']):
    #     viewwithboxes(img, j, numpages)

    # save outlined images into 'TEXTBOX_tiffs folder based on Document number'
    isWritten = cv2.imwrite(
        'TEXTBOX_tiffs/Doc{}/TextBoxDoc{}Page{}.tiff'.format(str(i), str(i), str(j)), img)
    # print('was saved = {}'.format(isWritten))

    # return userviewinput


def docblockanalysis(docblock, markers):
    # print(docblock)
    # words = re.findall(r'\w+', docblock) #regex (1) gets rid of special chars
    # regex (2) keeps special chars, could be used for identification
    sections = []
    section_dict = {}

    noWS_docblock = ' '.join(re.findall(r'\w+|\S+', docblock)).lower()

    # print('\n\n\t\t\tnoWS docblock:\n\n{}'.format(noWS_docblock))

    for i in range(len(markers)):
        if (i == 0):
            start = 0
        start = noWS_docblock.find(markers[i][0], start)
        end = noWS_docblock.find(markers[i][1], start)

        # prints all sections produced

        print(
            '\n\n\nNEW SECTION: \t{} -> {} \t\t {} -> {}\n'.format(markers[i][0], markers[i][1], start, end))
        print('{}'.format(noWS_docblock[start + len(markers[i][0]): end]))
        sections.append(noWS_docblock[start + len(markers[i][0]): end])
        # sections.append(' '.join(re.findall(r'\w+', noWS_docblock[start + len(markers[i][0]): end]))) #if extra symbols not needed (%symbols may be required)
    return sections

    # print(markers[0][0] in noWS_docblock)
    # print(markers[0][1] in noWS_docblock)
    # result1 = re.search(markers[0][0], noWS_docblock)
    # result2 = re.search(markers[0][1], noWS_docblock)
    # print(noWS_docblock)
    # print(markers[0][1])
    # print(result1)
    # print(result2)
    # searchstr = '{}(.*?){}'.format(markers[0][0], markers[0][1])
    # result = re.search(searchstr, noWS_docblock)
    # print(result)
    # for markpair in markers:
    #     result = re.search(markpair[0] + '(.*)' + markpair[1], noWS_docblock)
    #     if result:
    #         print('\t\t\tSECTION: \n\n{}'.format(result.group(1)))


def main():
    numberbiopsies = 1

    docblock = ''
    pageblocks = []
    docsdata = []
    pagemetadicts = []
    # sectionmarkers_new = ['clinical information provided', 'final diagnosis', 'light microscopy', 'immunofluorescence microscopy', 'electron microscopy', 'Gross Description', 'Frozen/Intraoperative Diagnosis: ()']
    # sectionmarkers_new = {'clinical information provided :': ['Specimen (s) Received :'], 'final diagnosis': ['kidney , biopsy :'], 'light microscopy': [
    # ], 'immunofluorescence microscopy': [], 'electron microscopy': [], 'Gross Description': [], 'Frozen/Intraoperative Diagnosis: ()': []}
    # sectionmarkers_new = {'clinical information provided :': [], 'specimen (s) received :': ['1 :', '2 :', '3 :'], 'final diagnosis': ['kidney , biopsy :', 'note :'], 'light microscopy :': [
    # ], 'immunofluorescence microscopy :': [], 'electron microscopy :': ['surgical pathology report', 'pathologist :'], 'gross description :': ['1 .', '2 .', '3 .'], 'Frozen /Intraoperative Diagnosis : ()': []}

 # possibly add "FINAL DIAGNOSIS    KIDNEY, BIOPSY:"
 # possibly add "FINAL DIAGNOSIS    KIDNEY, BIOPSY:"

    sectionmarkers_new = [['clinical information provided :', 'specimen (s) received :'], ['final diagnosis kidney , biopsy :', 'note :'], ['light microscopy :', 'immunofluorescence microscopy :'], ['immunofluorescence microscopy :', 'electron microscopy :'], [
        'electron microscopy :', 'pathologist :'], ['pathologist :', '* report electronically signed out *'], ['gross description :', 'frozen /intraoperative diagnosis : ()']]

    try:
        os.mkdir('TIFFS')
        os.mkdir('TEXTBOX_tiffs')
    except:
        pass

    for i in range(numberbiopsies):  # iterate through number of biopsies
        # images = convert_from_path('template_biopsy_copy{}.pdf'.format(
        #     str(i)))  # convert the pdf to a list of jpegs of the pages
        images = convert_from_path('BIO-01-003_FinalPathologyReport.pdf')

        try:
            os.mkdir('TIFFS/Doc{}'.format(str(i)))
            os.mkdir('TEXTBOX_tiffs/Doc{}'.format(str(i)))
        except:
            pass

        for j in range(len(images)):
            # save each jpeg of each page to tiff format
            images[j].save('TIFFS/Doc{}/Doc{}page{}.tiff'.format(str(i),
                                                                 str(i), str(j)), 'TIFF', quality=100)
            # images[j].save('Doc{}page{}.JPEG'.format(str(i), str(j)), 'JPEG', quality=100)

        for j in range(len(images)):  # now I want to convert to text using the library
            if j == 0:
                userin = ''

            # load images here and generate pytesseract dict here instead of in func
            # print(i)
            # print('working on Doc{}page{}.tiff'.format(i, j))
            img = cv2.imread('TIFFS/Doc{}/Doc{}page{}.tiff'.format(str(i), str(i), str(j)))
            textdict = pytesseract.image_to_data(img, output_type=Output.DICT)
            pagemetadicts.append(textdict)  # added for NEW HEADER DESTRCUTION FEATURE

            # FIND WAY TO GET RID OF HEADER --> TESTING SECTION
            useabletext = []
            for index, word in enumerate(textdict['text']):
                if(textdict['top'][index] in range(80, 2040)):
                    # print('"{}, top = {}"'.format(word, textdict['top'][index]))
                    useabletext.append(word)

                    # userin = tiff_to_textboxfiles(i, j, textdict, img, len(images), userin)
            tiff_to_textboxfiles(i, j, textdict, img, len(images))

            # userin, textdict = tiff_to_textboxfiles(i, j, len(images), userin)
            # pageblocks.append(' '.join(textdict['text']))
            pageblocks.append(' '.join(useabletext))

        docblock = ' '.join(pageblocks)
        # print('\n\n\n\t\t\tDOCBLOCK:\n\n'.format(docblock))
        docsdata.append(docblockanalysis(docblock, sectionmarkers_new))

        # print('\n\n\nFINAL TEXT BLOCK: \n\n{}'.format(docblock))

        # with docblock string, create func to analye string and break using docmarkers

    #         print('\n\n\t\t\tPRE STRIP : \n\n{}'.format(pageblock))
    #         print('\n\n\t\t\tPOST STRIP : \n\n{}'.format(pageblock.strip()))
    # print('\n\n\nFINAL TEXT BLOCK: \n\n{}'.format(docblock))
    # img = cv2.imread('tiff_reports/Doc{}page{}.tiff'.format(str(i), str(j)))
    # # img = grayscale(img)
    # # img = thresholding(img)  # idk what this does
    # pageinfodict = pytesseract.image_to_data(img, output_type=Output.DICT)
    # # creation of boxes
    # n_boxes = len(pageinfodict['text'])
    # for k in range(n_boxes):
    #     if int(float(pageinfodict['conf'][k])) > 60:
    #         (x, y, w, h) = (pageinfodict['left'][k], pageinfodict['top']
    #                         [k], pageinfodict['width'][k], pageinfodict['height'][k])
    #         img = cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    #
    # user_boxes = input('View text identified version of .tiff files? (Y/N)')
    # if(user_boxes in ['Y', 'yes', 'y', 'YES']):
    #     viewwithboxes(img, j, len(images))
    # temporary viewing
    # print('before imshow')
    # cv2.imshow('imgwithboxes', img)
    # cv2.waitKey(5000)
    # print('after imshow')
    # cv2.destroyAllWindows()
    # print(tempdict.keys())sd
    # print(tempdict.values())
    # print('\n\n\n')
main()
