from pdf2image import convert_from_path
import cv2
import pytesseract
from pytesseract import Output
import os
import re


class ScrapeDriver:
    def __init__(self):
        self.drivepath = '/Volumes/MoledinaLab-CC1032-MEDINT/Biobank 27890/Pathology Report PDF/'
        self.homepath = '/Users/anshulgowda/Documents/CODE/KUH2022/'
        self.pdfs = []
        self.sectionmarkers = [['clinical information provided :', 'specimen (s) received :'], ['final diagnosis kidney , biopsy :', 'note :'], ['light microscopy :', 'immunofluorescence microscopy :'], ['immunofluorescence microscopy :', 'electron microscopy :'], [
            'electron microscopy :', 'pathologist :'], ['pathologist :', '* report electronically signed out *'], [['gross description :', 'frozen /intraoperative diagnosis : ()'], ['gross description :', 'summary of stains performed and reviewed']]]
        self.i = 0
        self.j = 0
        self.docsdata = []

    def CreatePatch(self):
        try:
            os.chdir(self.drivepath)
            print('working directory changed to:\t{}'.format(os.getcwd()))
            return True
        except OSError:
            print('unable to connect to share drive ({})\ncurrent working directory: {}'.format(
                self.drivepath, os.getcwd()))
            return False

    def DestroyPatch(self):
        try:
            os.chdir(self.homepath)
            print('working directory changed to:\t{}'.format(os.getcwd()))
            return True
        except OSError:
            print('unable to connect to return to home directory ({})\ncurrent working directory: {}'.format(
                self.drivepath, os.getcwd()))
            return False

    def PullFiles(self):
        if(self.CreatePatch()):  # create patch to share drive
            pdflist = os.listdir(os.getcwd())
            # return list of full paths
            # self.pdfs = [self.homepath + filename for filename in pdflist]
            self.pdfs = [filename for filename in pdflist]
            return True

        else:
            return False

    def tiff_to_textboxfiles(self, pageinfodict, img, numpages):
        n_boxes = len(pageinfodict['text'])
        for k in range(n_boxes):
            if int(float(pageinfodict['conf'][k])) > 60:
                (x, y, w, h) = (pageinfodict['left'][k], pageinfodict['top']
                                [k], pageinfodict['width'][k], pageinfodict['height'][k])
                img = cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

        isWritten = cv2.imwrite(
            'TEXTBOX_tiffs/Doc{}/TextBoxDoc{}Page{}.tiff'.format(str(self.i), str(self.i), str(self.j)), img)

    def docblockanalysis(self, docblock):
        sections = []
        section_dict = {}

        noWS_docblock = ' '.join(re.findall(r'\w+|\S+', docblock)).lower()
        print('\n\n\n\t\t\t DOC BLOCK GENERATED FOR DOC#{}:\n\n{}'.format(self.i, noWS_docblock))

        for z in range(len(self.sectionmarkers)):
            # whichmarker 0
            whichone = []
            ifmultiple = [False, False]
            if (z == 0):
                start = 0

            if(isinstance(self.sectionmarkers[z][0], list)):
                if(noWS_docblock.find(self.sectionmarkers[z][0][0], start) > 0):
                    start = noWS_docblock.find(self.sectionmarkers[z][0][0], start)
                    whichmarker = 0
                    whichone[0] = 0
                    print('\n\n\nNEW SECTION of DOC{}: \t{} -> {} \t\t {} -> {}\n'.format(self.i,
                                                                                          self.sectionmarkers[z][0], self.sectionmarkers[z][1], start, end))
                    print('{}'.format(noWS_docblock[start +
                                                    len(self.sectionmarkers[self.i][0]): end]))
                else:
                    start = noWS_docblock.find(self.sectionmarkers[z][0][1], start)
                    whichmarker = 1
                    whichone[0] = 1
            else:
                start = noWS_docblock.find(self.sectionmarkers[z][0], start)

            if(isinstance(self.sectionmarkers[z][1], list)):
                if(noWS_docblock.find(self.sectionmarkers[z][1][0], start) > 0):
                    end = noWS_docblock.find(self.sectionmarkers[z][1][0], start)
                    whichone[1] = 0
                else:
                    end = noWS_docblock.find(self.sectionmarkers[z][1][1], start)
                    whichone[1] = 1
            else:
                end = noWS_docblock.find(self.sectionmarkers[z][1], start)

            # try:
            #     start = noWS_docblock.find(self.sectionmarkers[z][0], start)
            # except TypeError:
            #     if(noWS_docblock.find(self.sectionmarkers[z][0][0], start) > 0):
            #         start = noWS_docblock.find(self.sectionmarkers[z][0][0], start)
            #         whichmarker = 0
            #     else:
            #         start = noWS_docblock.find(self.sectionmarkers[z][0][1], start)
            #         whichmarker = 1
            #
            #
            #     end = noWS_docblock.find(self.sectionmarkers[z][1], start)
            # except TypeError:
            #     if(noWS_docblock.find(self.sectionmarkers[z][1][0], start) > 0):
            #         end = noWS_docblock.find(self.sectionmarkers[z][1][0], start)
            #     else:
            #         end = noWS_docblock.find(self.sectionmarkers[z][1][1], start)

            print('\n\n\nNEW SECTION of DOC{}: \t{} -> {} \t\t {} -> {}\n'.format(self.i,
                                                                                  self.sectionmarkers[z][0], self.sectionmarkers[z][1], start, end))

            if(isinstance(self.sectionmarkers[self.i][0], list)):
                print('{}'.format(
                    noWS_docblock[start + len(self.sectionmarkers[self.i][0][whichmarker]): end]))
                sections.append(
                    noWS_docblock[start + len(self.sectionmarkers[z][0][whichmarker]): end])
            else:
                print('{}'.format(noWS_docblock[start + len(self.sectionmarkers[self.i][0]): end]))
                sections.append(noWS_docblock[start + len(self.sectionmarkers[z][0]): end])

            # if extra symbols not needed (%symbols may be required):
            # sections.append(' '.join(re.findall(r'\w+', noWS_docblock[start + len(markers[i][0]): end])))

        return sections

    def Scrape(self, filename):
        pageblocks = []
        print('entered scrape')

        if(self.DestroyPatch):
            # open specified file, presumably generated by PullFiles
            self.CreatePatch()
            images = convert_from_path(filename)
            self.DestroyPatch()

            try:
                os.mkdir('TIFFS')
                os.mkdir('TEXTBOX_tiffs')
            except:
                print('\n\nfailed try where folders are made \n\n')
                pass
            try:
                os.mkdir('TIFFS/Doc{}'.format(self.i))
                os.mkdir('TEXTBOX_tiffs/Doc{}'.format(self.i))
            except:
                print('\n\nfailed try where subfoldersare made\n\n')

            print('entered scrape')

            for j in range(len(images)):  # iterate through images and save them locally in KUH2022 as .tiffs
                images[j].save('TIFFS/Doc{}/Doc{}page{}.tiff'.format(str(self.i),
                                                                     str(self.i), str(j)), 'TIFF', quality=100)

            for j in range(len(images)):  # 2nd iteration to begin the scraping
                self.j = j
                if j == 0:
                    userin = ''

                # "i" will be passed in, i will be generated in main
                img = cv2.imread(
                    'TIFFS/Doc{}/Doc{}page{}.tiff'.format(str(self.i), str(self.i), str(self.j)))
                # produce pytesseract ML text dictionary
                textdict = pytesseract.image_to_data(img, output_type=Output.DICT)

                # produce ML generated boxes around selected text
                self.tiff_to_textboxfiles(textdict, img, len(images))
                # produce dictionary of all "text" as ascertained by pytesseract
                pageblocks.append(' '.join(textdict['text']))
                docblock = ' '.join(pageblocks)

                # print('\n\n\n\t\t\t DOC BLOCK GENERATED FOR DOC#{}:\n\n{}'.format(self.i, docblock))  # purely testing

                # would be replaced by code that writes it out to .xls file
                # add list of section data into overarching docs list
            self.docsdata.append(self.docblockanalysis(docblock))

    def AnalyzePdfs(self):
        self.i = 0
        for doc in self.pdfs:
            userin = input('continue {} -> {}'.format(self.i, self.i+1))
            if(userin.lower() in ['n', 'no']):
                return
            path, extension = os.path.splitext(doc)
            print('extension = {}\n'.format(extension))
            if(extension.lower() == '.pdf'):
                print('\n\t\tscraping {}\n'.format(path + extension))
                self.Scrape(doc)  # UNCOMMENT!!!!!!!!
                self.i += 1
        # pdflist = os.listdir(os.getcwd())
        # for j in [homepath + i for i in pdflist]:
        #     # double check this works
        #     path, extension = os.path.splitext()
        #     if(extension.lower() == '.pdf'):
        #         Scrape(j)
        #         pass  # calling Scrape on the individual pdfs


def main():
    Drive = ScrapeDriver()
    Drive.PullFiles()  # load files into pdfs attribute, WORKS
    Drive.AnalyzePdfs()
    print('\n\n\t\t SUMMARY: number of docs read = ({}) == ({})\n\n'.format(len(Drive.docsdata), Drive.i))
    counter = 0

    print('#doc = {}'.format(Drive.i))

    for i in Drive.docsdata:
        print('DATA Dump for doc{}:\n{}\n\n'.format(counter, i))
        counter += 1

    # sectionmarkers_new = [['clinical information provided :', 'specimen (s) received :'], ['1 :', '2 :'], ['2 :', '3 :'], ['3 :', 'final diagnosis'], ['kidney , biopsy :', 'note :'], ['note :', 'light microscopy :'], ['light microscopy :', 'immunofluorescence microscopy :'], ['immunofluorescence microscopy :', 'electron microscopy :'], [
    #     'electron microscopy :', 'surgical pathology report'], ['surgical pathology report', 'pathologist :'], ['pathologist :', 'gross description :'], ['1 .', '2 .'], ['2 .', '3 .'], ['3 .', 'frozen /intraoperative diagnosis : ()'], ['frozen /intraoperative diagnosis : ()', '-999999999']]
    #
    # drivepath = '/Volumes/MoledinaLab-CC1032-MEDINT/Biobank 27890/Pathology Report PDF/'
    # homepath = '/Users/anshulgowda/Documents/CODE/KUH2022/'
    # print('working directory: {}'.format(os.getcwd()))
    # os.chdir('/Volumes/MoledinaLab-CC1032-MEDINT/Biobank 27890/Pathology Report PDF/')
    # # os.chdir('/Users/anshulgowda/Documents/CODE/KUH2022/')
    # print('working directory: {}'.format(os.getcwd()))
    #
    # pdflist = os.listdir(os.getcwd())
    # for j in [drivepath + i for i in pdflist]:
    #     print('\n\n{}\n\n'.format(j))


    # for filename in os.listdir(os.getcwd()):
    # call the read pdf funcs in "jpegtotext.py" prolly need to rename the file to
    # "biopsyscraper.py"
main()
