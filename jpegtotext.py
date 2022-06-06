from PIL import *
from pdf2image import convert_from_path
import cv2
import pytesseract
from pytesseract import Output
import os


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
    return userviewinput


def main():
    numberbiopsies = 1

    outputstring = ''
    try:
        os.mkdir('TIFFS')
        os.mkdir('TEXTBOX_tiffs')
    except:
        pass

    for i in range(numberbiopsies):
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
            userin = tiff_to_textboxfiles(i, j, len(images), userin)

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
