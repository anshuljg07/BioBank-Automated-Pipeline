from PIL import *
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


def tiff_to_textboxfiles(i, j, numpages, userviewinput):
    img = cv2.imread('TIFFS/Doc{}/Doc{}page{}.tiff'.format(str(i), str(i), str(j)))
    # img = grayscale(img)
    # img = thresholding(img)  # idk what this does
    pageinfodict = pytesseract.image_to_data(img, output_type=Output.DICT)
    # creation of boxes
    n_boxes = len(pageinfodict['text'])
    for k in range(n_boxes):
        if int(float(pageinfodict['conf'][k])) > 60:
            (x, y, w, h) = (pageinfodict['left'][k], pageinfodict['top']
                            [k], pageinfodict['width'][k], pageinfodict['height'][k])
            img = cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    if not userviewinput:
        userviewinput = input('View text identified version of .tiff files? (Y/N)')
    if(userviewinput in ['Y', 'yes', 'y', 'YES']):
        viewwithboxes(img, j, numpages)

    # save outlined images into 'TEXTBOX_tiffs folder based on Document number'
    isWritten = cv2.imwrite(
        'TEXTBOX_tiffs/Doc{}/TextBoxDoc{}Page{}.tiff'.format(str(i), str(i), str(j)), img)
    # print('was saved = {}'.format(isWritten))

    return userviewinput, pageinfodict


def docblockanalysis(docblock, markers):
    # print(docblock)
    # words = re.findall(r'\w+', docblock) #regex (1) gets rid of special chars
    # regex (2) keeps special chars, could be used for identification
    sections = []

    noWS_docblock = ' '.join(re.findall(r'\w+|\S+', docblock)).lower()
    print(noWS_docblock)

    print(len(markers))

    # start = noWS_docblock.find(markers[9][0], start)   #creation of old start, use when iteration is there
    # start = noWS_docblock.find(markers[14][0])
    # end = noWS_docblock.find(markers[14][1], start)
    #
    # print('{} -> {} = {} -> {}'.format(markers[14][0], markers[14][1], start, end))
    # print(noWS_docblock[start + len(markers[14][0]): end])

    for i in range(len(markers)):
        if (i == 0):
            start = 0
        start = noWS_docblock.find(markers[i][0], start)
        end = noWS_docblock.find(markers[i][1], start)
        print(
            '\n\n\nNEW SECTION: \t{} -> {} \t\t {} -> {}\n'.format(markers[i][0], markers[i][1], start, end))
        sections.append(noWS_docblock[start + len(markers[14][0]): end])
        print(noWS_docblock[start + len(markers[i][0]): end])

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
    # sectionmarkers_new = ['clinical information provided', 'final diagnosis', 'light microscopy', 'immunofluorescence microscopy', 'electron microscopy', 'Gross Description', 'Frozen/Intraoperative Diagnosis: ()']
    # sectionmarkers_new = {'clinical information provided :': ['Specimen (s) Received :'], 'final diagnosis': ['kidney , biopsy :'], 'light microscopy': [
    # ], 'immunofluorescence microscopy': [], 'electron microscopy': [], 'Gross Description': [], 'Frozen/Intraoperative Diagnosis: ()': []}
    # sectionmarkers_new = {'clinical information provided :': [], 'specimen (s) received :': ['1 :', '2 :', '3 :'], 'final diagnosis': ['kidney , biopsy :', 'note :'], 'light microscopy :': [
    # ], 'immunofluorescence microscopy :': [], 'electron microscopy :': ['surgical pathology report', 'pathologist :'], 'gross description :': ['1 .', '2 .', '3 .'], 'Frozen /Intraoperative Diagnosis : ()': []}
 # specimen (s) received :
 # specimen (s) received :
    sectionmarkers_new = [['clinical information provided :', 'specimen (s) received :'], ['1 :', '2 :'], ['2 :', '3 :'], ['3 :', 'final diagnosis'], ['kidney , biopsy :', 'note :'], ['note :', 'light microscopy :'], ['light microscopy :', 'immunofluorescence microscopy :'], [
        'immunofluorescence microscopy :', 'electron microscopy :'], ['electron microscopy :', 'surgical pathology report'], ['surgical pathology report', 'pathologist :'], ['pathologist :', 'gross description :'], ['1 .', '2 .'], ['2 .', '3 .'], ['3 .', 'frozen /intraoperative diagnosis : ()'], ['frozen /intraoperative diagnosis : ()', '-999999999']]

    try:
        os.mkdir('TIFFS')
        os.mkdir('TEXTBOX_tiffs')
    except:
        pass

    for i in range(numberbiopsies):  # iterate through number of biopsies
        images = convert_from_path('template_biopsy_copy{}.pdf'.format(
            str(i)))  # convert the pdf to a list of jpegs of the pages
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
            userin, textdict = tiff_to_textboxfiles(i, j, len(images), userin)
            pageblocks.append(' '.join(textdict['text']))
            # print('\n\n\t\t\tPRE STRIP : \n\n{}'.format(pageblocks[j]))
            # print('\n\n\t\t\tPOST STRIP : \n\n{}'.format(pageblocks[j]))

        docblock = ' '.join(pageblocks)
        docblockanalysis(docblock, sectionmarkers_new)
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
