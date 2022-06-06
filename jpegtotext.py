from PIL import *
from pdf2image import convert_from_path
import cv2
import pytesseract
from pytesseract import Output


def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


numberbiopsies = 1

outputstring = ''

for i in range(numberbiopsies):
    images = convert_from_path('template_biopsy_copy{}.pdf'.format(
        str(i)))  # convert the pdf to a list of jpegs of the pages

    for j in range(len(images)):
        # save each jpeg of each page to tiff format
        images[j].save('Doc{}page{}.tiff'.format(str(i), str(j)), 'TIFF', quality=100)
        # images[j].save('Doc{}page{}.JPEG'.format(str(i), str(j)), 'JPEG', quality=100)

    for j in range(len(images)):  # now I want to convert to text using the library
        img = cv2.imread('Doc{}page{}.tiff'.format(str(i), str(j)))
        img = grayscale(img)
        img = thresholding(img)  # idk what this does
        tempdict = pytesseract.image_to_data(img, output_type=Output.DICT)
        print(tempdict.keys())
        print(tempdict.values())
        print('\n\n\n')
