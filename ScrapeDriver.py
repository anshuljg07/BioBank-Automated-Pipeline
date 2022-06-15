from pdf2image import convert_from_path
import cv2
import pytesseract
from pytesseract import Output
import os
import re
import pandas as pd
import openpyxl


class ScrapeDriver:
    def __init__(self):
        self.drivepath = '/Volumes/MoledinaLab-CC1032-MEDINT/Biobank 27890/Pathology Report PDF/'
        self.homepath = '/Users/anshulgowda/Documents/CODE/KUH2022/'
        self.pdfs = []
        self.sectionmarkers = [['clinical information provided :', 'specimen (s) received :'], [['final diagnosis ', 'note :'], ['final diagnosis ', 'light microscopy :'], ['final diagnosis ', 'pathologist :']], [['light microscopy :', 'immunofluorescence microscopy :'], ['light microscopy :', 'immunofluorescence :'], ['light microscopy :', 'electron microscopy :'], ['light microscopy :', 'pathologist :']], [['immunofluorescence microscopy :', 'electron microscopy :'], ['immunofluorescence :', 'electron microscopy :'], ['immunofluorescence microscopy :', 'pathologist :']], [
            'electron microscopy :', 'pathologist :'], ['pathologist :', '* report electronically signed out *'], [['gross description :', 'frozen /intraoperative diagnosis : ()'], ['gross description :', 'summary of stains performed and reviewed']]]
        self.i = 0
        self.j = 0
        self.docsdata = []
        self.error = {}
        self.docsread = []
        self.docstesting = ['0099', '0013', '0016', '0025', '0028', '0059', '0073',
                            '0107', '0128', '0161', '0189', '0213', '0276', '0282', '0302', '0306', '0307']

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

    def tiff_to_textboxfiles(self, pageinfodict, img, numpages, uniqueID):
        n_boxes = len(pageinfodict['text'])
        for k in range(n_boxes):
            if int(float(pageinfodict['conf'][k])) > 60:
                (x, y, w, h) = (pageinfodict['left'][k], pageinfodict['top']
                                [k], pageinfodict['width'][k], pageinfodict['height'][k])
                img = cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

        isWritten = cv2.imwrite(
            'TEXTBOX_tiffs/Doc{}/TextBoxDoc{}Page{}.tiff'.format(str(self.i), str(self.i), str(self.j)), img)
        isWritten = cv2.imwrite(
            'TEXTBOX_tiffs/{}/TextBox{}Page{}.tiff'.format(uniqueID, uniqueID, str(self.j)), img)

    def docblockanalysis(self, docblock):
        sections = []
        section_dict = {}

        noWS_docblock = ' '.join(re.findall(r'\w+|\S+', docblock)).lower()
        # print('\n\n\n\t\t\t DOC BLOCK GENERATED FOR DOC#{}:\n{}'.format(self.i, noWS_docblock)) #uncomment for docblock

        optionsdict = {}

        for z in range(len(self.sectionmarkers)):
            if (z == 0):
                start = 0
            if(isinstance(self.sectionmarkers[z][0], type([]))):
                # print('option = {}'.format(self.sectionmarkers[z]))
                # print('marker {} has multiple options'.format(z))
                numoptions = len(self.sectionmarkers[z])

                for j, options in enumerate(self.sectionmarkers[z]):
                    oldstart = start
                    start = noWS_docblock.find(self.sectionmarkers[z][j][0], start)
                    end = noWS_docblock.find(self.sectionmarkers[z][j][1], start)

                    if(start > 0 and end > 0):
                        optionsdict[z] = j
                        sections.append(
                            noWS_docblock[start + len(self.sectionmarkers[z][j][0]): end])
                        # uncomment to print section shit
                        # print('\nNEW SECTION of DOC{}: \t{} -> {} \t\t {} -> {}'.format(self.i,
                        # self.sectionmarkers[z][j][0], self.sectionmarkers[z][j][1], start, end))
                        break

                    # to account for when "Gross Description:" occurs but no other headers follow
                    if(start > 0 and end < 0 and self.sectionmarkers[z][j][0] == "gross description :" and j == len(self.sectionmarkers[z]) - 1):
                        sections.append(
                            noWS_docblock[start + len(self.sectionmarkers[z][j][0]): end])
                        break
                    if(start < 0 and self.sectionmarkers[z][j][0] != "gross description :" and j == len(self.sectionmarkers[z]) - 1):
                        sections.append(' ')
                        start = oldstart
                        break

                    if(start < 0):
                        start = oldstart  # reset start to a non-negative number

                # if(start < 0 or end < 0):
                #     sections.append(' ')
                #     start = oldstart
                #     self.error[self.i] = [self.docsread[self.i], self.sectionmarkers[z], start, end]

                if(start < 0 and end < 0):
                    sections.append(' ')
                    start = oldstart
                    self.error[self.i] = [self.docsread[self.i], self.sectionmarkers[z], start, end]

                # uncomment to print string added to section
                # print('{}\n'.format(noWS_docblock[start + len(self.sectionmarkers[z][j][0]): end]))

            else:
                oldstart = start
                start = noWS_docblock.find(self.sectionmarkers[z][0], start)
                end = noWS_docblock.find(self.sectionmarkers[z][1], start)
                # print('\nNEW SECTION of DOC{}: \t{} -> {} \t\t {} -> {}'.format(self.i,
                # self.sectionmarkers[z][0], self.sectionmarkers[z][1], start, end))
                if(start < 0 or end < 0):
                    start = oldstart
                    self.error[self.i] = [self.docsread[self.i], self.sectionmarkers[z], start, end]
                    sections.append(' ')
                    continue

                sections.append(noWS_docblock[start + len(self.sectionmarkers[z][0]): end])

                # print('{}\n'.format(noWS_docblock[start + len(self.sectionmarkers[z][0]): end]))

        return sections

    def Scrape(self, filename, uniqueID):
        pageblocks = []
        # print('entered scrape')

        if(self.DestroyPatch):
            # open specified file, presumably generated by PullFiles
            self.CreatePatch()
            images = convert_from_path(filename)
            self.DestroyPatch()

            try:
                os.mkdir('TIFFS')
                os.mkdir('TEXTBOX_tiffs')
            except:
                # print('\n\nfailed try where folders are made \n\n')
                pass
            try:
                # os.mkdir('TIFFS/Doc{}'.format(self.i))
                # os.mkdir('TEXTBOX_tiffs/Doc{}'.format(self.i))
                os.mkdir('TIFFS/{}'.format(uniqueID))
                os.mkdir('TEXTBOX_tiffs/{}'.format(uniqueID))
            except:
                pass
                # print('\n\nfailed try where subfoldersare made\n\n')

            for j in range(len(images)):  # iterate through images and save them locally in KUH2022 as .tiffs
                # images[j].save('TIFFS/Doc{}/Doc{}page{}.tiff'.format(str(self.i), str(self.i), str(j)), 'TIFF', quality=100)
                images[j].save('TIFFS/{}/{}page{}.tiff'.format(uniqueID,
                                                               uniqueID, str(j)), 'TIFF', quality=100)

            for j in range(len(images)):  # 2nd iteration to begin the scraping
                self.j = j
                if j == 0:
                    userin = ''

                # "i" will be passed in, i will be generated in main
                # img = cv2.imread('TIFFS/Doc{}/Doc{}page{}.tiff'.format(str(self.i), str(self.i), str(self.j)))
                img = cv2.imread('TIFFS/{}/{}page{}.tiff'.format(uniqueID, uniqueID, str(self.j)))

                # produce pytesseract ML text dictionary
                textdict = pytesseract.image_to_data(img, output_type=Output.DICT)

                # produce ML generated boxes around selected text
                self.tiff_to_textboxfiles(textdict, img, len(images), uniqueID)

                # GET RID OF HEADER
                useabletext = []
                for index, word in enumerate(textdict['text']):
                    if(textdict['top'][index] in range(80, 2040)):
                        # print('"{}, top = {}"'.format(word, textdict['top'][index]))
                        useabletext.append(word)

                # produce dictionary of all "text" as ascertained by pytesseract
                pageblocks.append(' '.join(useabletext))
                docblock = ' '.join(pageblocks)

                # OLD FEATURE: produce dictionary of all "text" as ascertained by pytesseract
                # pageblocks.append(' '.join(textdict['text']))
                #
                # docblock = ' '.join(pageblocks)

                # print('\n\n\n\t\t\t DOC BLOCK GENERATED FOR DOC#{}:\n\n{}'.format(self.i, docblock))  # purely testing

                # would be replaced by code that writes it out to .xls file
                # add list of section data into overarching docs list
            self.docsdata.append(self.docblockanalysis(docblock))

    def AnalyzePdfs(self):
        self.i = 0
        for doc in self.pdfs:
            # userin=input('continue {} -> {}'.format(self.i, self.i+1))
            # if(userin.lower() in ['n', 'no']):
            #     return
            path, extension = os.path.splitext(doc)
            # print('extension = {}\n'.format(extension))

            # FIND WAY TO GET ID FROM filename
            uniqueID = path[path.find('-', 4)+1:path.find('_')]
            if (len(uniqueID) < 4):
                uniqueID = '0' + uniqueID

            # if(extension.lower() == '.pdf' and uniqueID in self.docstesting):
            if(extension.lower() == '.pdf' and uniqueID not in self.docsread):
                # nextdoc = input('Ready for "Report {}"\n?> '.format(uniqueID))
                # if(nextdoc.lower() in ['y', 'yes']):
                # print('\n\t\tscraping {}\n'.format(path + extension))
                print('\n\t\tscraping {}\n'.format(uniqueID))
                self.docsread.append(uniqueID)
                self.Scrape(doc, uniqueID)  # UNCOMMENT!!!!!!!!
                self.i += 1

    def WritetoXLSX(self):
        self.DestroyPatch()
        try:
            os.mkdir('xlsfiles')
        except:
            pass

        rownames = ['clinical information provided', 'final diagnosis', 'light microscopy',
                    'immunofluorescence microscopy', 'electron microscopy', 'pathologist', 'gross description']
        biopsydf = pd.DataFrame(self.docsdata, index=self.docsread, columns=rownames)
        biopsydf.to_excel('xlsfiles/biobankrepo.xlsx', sheet_name='biobank scraped pdfs')
        return


def main():
    Drive = ScrapeDriver()
    Drive.PullFiles()  # load files into pdfs attribute, WORKS
    Drive.AnalyzePdfs()
    print('\n\n\t\t SUMMARY: number of docs read = ({}) == ({})\n\n'.format(len(Drive.docsdata), Drive.i))
    Drive.WritetoXLSX()
    counter = 0

    # print('#doc = {}'.format(Drive.i))
    userin = input("ready for error output?\n?>")
    if(userin.lower() in ['y', 'yes']):
        for key, value in Drive.error.items():
            print(value)


main()
