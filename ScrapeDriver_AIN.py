from pdf2image import convert_from_path
import cv2
import pytesseract
from pytesseract import Output
import os
import re
import pandas as pd
import openpyxl
import sqlite3


class ScrapeDriver:
    def __init__(self):
        self.drivepath = '/Volumes/MoledinaLab-CC1032-MEDINT/AIN 9286/Biopsy reports/Biopsy Reports/'
        self.sitefolders = ['Site-1-001-100/', 'Site-1-100-200/',
                            'Site-1-201-300/', 'Site-1-301-400/', 'Site-2-001-100/']
        # self.procesedpath = '/Volumes/MoledinaLab-CC1032-MEDINT/Biobank 27890/Pathology Report PDF Analyzed'
        # self.drivepath = '/Volumes/MoledinaLab-CC1032-MEDINT/Biobank 27890/Pathology Report PDF Staging'
        self.homepath = '/Users/anshulgowda/Documents/CODE/KUH2022/'
        self.pdfs = []

        # TODO: replace with AIN section markers
        self.sectionmarkers = [['clinical information provided :', 'specimen (s) received :'], ['final diagnosis ', 'pathologist :'], ['pathologist :', '* report electronically signed out *'], [
            ['light microscopy :', 'electron microscopy :'], ['light microscopy :', 'interpretation']], [['electron microscopy :', 'interpretation'], ['electron microscopy :', 'immunofluorescence']], ['immunofluorescence microscopy :', 'interpretation']]

        # self.sectionmarkers = [['clinical information provided :', 'specimen (s) received :'], [['final diagnosis ', 'note :'], ['final diagnosis ', 'light microscopy :'], ['final diagnosis ', 'pathologist :']], [['light microscopy :', 'immunofluorescence microscopy :'], ['light microscopy :', 'immunofluorescence :'], ['light microscopy :', 'electron microscopy :'], ['light microscopy :', 'pathologist :']], [['immunofluorescence microscopy :', 'electron microscopy :'], ['immunofluorescence :', 'electron microscopy :'], ['immunofluorescence microscopy :', 'pathologist :']], [
        #     'electron microscopy :', 'pathologist :'], ['pathologist :', '* report electronically signed out *'], [['gross description :', 'frozen /intraoperative diagnosis : ()'], ['gross description :', 'summary of stains performed and reviewed']]]
        self.i = 0
        self.j = 0
        self.docsdata = []
        self.dbconnection = None
        self.error = {}
        self.docsread = []

        # TODO: add some docs to the testing list
        # self.docstesting = ['01-0001', '01-0028', '01-0097', '01-0159']
        self.docstesting = ['01-0001', '01-0028', '01-0097', '01-0159', '01-0172', '01-0194', '01-0209',
                            '01-0228', '01-0271', '01-0286', '01-0304', '01-0311', '02-0014', '02-0024', '02-0066', '02-0080']
        # self.docstesting = ['0099', '0013', '0016', '0025', '0028', '0059', '0073',
        #                     '0107', '0128', '0161', '0189', '0213', '0276', '0282', '0302', '0306', '0307']

    '''
    Create patch to the staging directory by chaging cwd to the shared drive specified by the drivepath attribute
    '''

    def CreatePatch(self):
        try:
            os.chdir(self.drivepath)
            print('working directory changed to:\t{}'.format(os.getcwd()))
            return True
        except OSError:
            print('unable to connect to share drive ({})\ncurrent working directory: {}'.format(
                self.drivepath, os.getcwd()))
            return False

    '''
    Destroy patch to the staging directory by changing back to project directory using the homepath attribute
    '''

    def DestroyPatch(self):
        try:
            os.chdir(self.homepath)
            print('working directory changed to:\t{}'.format(os.getcwd()))
            return True
        except OSError:
            print('unable to connect to return to home directory ({})\ncurrent working directory: {}'.format(
                self.drivepath, os.getcwd()))
            return False

    '''
    Pull all files from the specific sitefolders using the patch and load them into the pdfs attribute. Stored in {sitefolder}/{docnumber}
    format.
    '''

    def PullFiles(self):
        if(self.CreatePatch()):  # create patch to share drive
            for sitefolder in self.sitefolders:  # iterate through the site folders and load into pdflist
                os.chdir(self.drivepath + sitefolder)
                pdflist = os.listdir(os.getcwd())
                pdflist = [sitefolder + doc for doc in pdflist]
                self.pdfs.extend(pdflist)

            # os.chdir(self.drivepath)
            # pdflist = os.listdir(os.getcwd())
            # self.pdfs = [filename for filename in pdflist]
            return True

        else:
            return False

    '''
    Using the meta/concrete data generated from pytesseract ML query, create visual boxes around the locations
    deemed text by pytesseract. These boxed versions are then saved into the "TEXTBOX_tiffs" directory by the number
    were processed. Not required for the scraping feature, but used for debugging and cool af!
    '''

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

    '''
    Takes a block of string that was scraped from the pdf and then using regex will search for all non whitespace chars
    and then pull out the relevant text using a priority based system of common section headers
    '''

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
                        # uncomment to print section stuff
                        print('\nNEW SECTION of DOC{}: \t{} -> {} \t\t {} -> {}'.format(self.i,
                                                                                        self.sectionmarkers[z][j][0], self.sectionmarkers[z][j][1], start, end))
                        break

                    # to account for when "Gross Description:" occurs but no other headers follow
                    # if(start > 0 and end < 0 and self.sectionmarkers[z][j][0] == "gross description :" and j == len(self.sectionmarkers[z]) - 1):
                    #     sections.append(
                    #         noWS_docblock[start + len(self.sectionmarkers[z][j][0]): end])
                    #     break
                    # if(start < 0 and self.sectionmarkers[z][j][0] != "gross description :" and j == len(self.sectionmarkers[z]) - 1):
                    #     sections.append(' ')
                    #     start = oldstart
                    #     break

                    if(start > 0 and end < 0 and self.sectionmarkers[z][j][0] == 'immunofluorescence microscopy :' and j == len(self.sectionmarkers[z]) - 1):
                        sections.append(
                            noWS_docblock[start + len(self.sectionmarkers[z][j][0]): end])
                        break
                    if(start < 0 and self.sectionmarkers[z][j][0] != 'immunofluorescence microscopy :' and j == len(self.sectionmarkers[z]) - 1):
                        sections.append(' ')
                        start = oldstart
                        break

                    if(start < 0):
                        start = oldstart  # reset start to a non-negative number

                if(start < 0 and end < 0):
                    sections.append(' ')
                    start = oldstart
                    self.error[self.i] = [self.docsread[self.i], self.sectionmarkers[z], start, end]

                # uncomment to print string added to section
                print('{}\n'.format(noWS_docblock[start + len(self.sectionmarkers[z][j][0]): end]))

            else:
                oldstart = start
                start = noWS_docblock.find(self.sectionmarkers[z][0], start)
                end = noWS_docblock.find(self.sectionmarkers[z][1], start)
                print('\nNEW SECTION of DOC{}: \t{} -> {} \t\t {} -> {}'.format(self.i,
                                                                                self.sectionmarkers[z][0], self.sectionmarkers[z][1], start, end))
                if(start < 0 or end < 0):
                    start = oldstart
                    self.error[self.i] = [self.docsread[self.i], self.sectionmarkers[z], start, end]
                    sections.append(' ')
                    continue

                sections.append(noWS_docblock[start + len(self.sectionmarkers[z][0]): end])

                # uncomment to print string added to section
                print('{}\n'.format(noWS_docblock[start + len(self.sectionmarkers[z][0]): end]))

        return sections

    '''
    Make the optional directories to store the in transition files, and convert the pdfs to imgs. Then they will
    be saved in these directories based upon their uniqueID BIO-XX-XXXX, but only the four last XXXX are used. The
    text scraping ML algo is applied and sent to docblockanalysis(). The resulting text is added to a list where all
    the relevant info is stored for each doc.
    '''

    def Scrape(self, filename, uniqueID):
        pageblocks = []

        if(self.DestroyPatch):
            # open specified file, presumably generated by PullFiles
            self.CreatePatch()
            images = convert_from_path(filename)  # convert the pdfs to imgs
            self.DestroyPatch()

            try:
                os.mkdir('AIN_TIFFS')
                os.mkdir('AIN_TEXTBOX_tiffs')
            except:
                pass
            try:
                os.mkdir('AIN_TIFFS/{}'.format(uniqueID))
                os.mkdir('AIN_TEXTBOX_tiffs/{}'.format(uniqueID))
            except:
                pass

            for j in range(len(images)):  # iterate through images and save them locally in KUH2022 as .tiffs
                images[j].save('AIN_TIFFS/{}/{}page{}.tiff'.format(uniqueID,
                                                                   uniqueID, str(j)), 'TIFF', quality=100)

            for j in range(len(images)):  # 2nd iteration to begin the scraping
                self.j = j
                if j == 0:
                    userin = ''

                # "i" will be passed in, i will be generated in main
                img = cv2.imread(
                    'AIN_TIFFS/{}/{}page{}.tiff'.format(uniqueID, uniqueID, str(self.j)))

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

            # print(docblock)
            # would be replaced by code that writes it out to .xls file
            # add list of section data into overarching docs list
            self.docsdata.append(self.docblockanalysis(docblock))

    '''
    Standardizes the uniqueID for documents that have XXX instead of XXXX. The documents that are .pdf are Then
    analyzed using the Scrape() function.
    '''

    def AnalyzePdfs(self):
        self.i = 0
        for doc in self.pdfs:
            # userin = input('continue {} -> {}\n?> '.format(self.i, self.i+1))
            # if(userin.lower() in ['n', 'no']):
            #     return
            path, extension = os.path.splitext(doc)

            # uniqueID = path[path.find('-', 4)+1:path.find('_')]
            uniqueID = path.split('/')[1]

            if (len(uniqueID.split('-')[1]) < 4):
                uniqueID = uniqueID.split('-')[0] + '-0' + uniqueID.split('-')[1]

            # if(extension.lower() == '.pdf' and uniqueID in self.docstesting):
            # if(extension.lower() == '.pdf' and uniqueID not in self.docsread and uniqueID in self.docstesting):
            if(extension.lower() == '.pdf' and uniqueID not in self.docsread):
                # userin = input('continue {} -> {}\n?> '.format(self.i, self.i+1))
                # if(userin.lower() in ['n', 'no']):
                #     return
                # print('\n\t\tscraping {}\n'.format(path + extension))
                print('\n\t\tscraping {}, ID = {}\n'.format(doc, uniqueID))
                self.docsread.append(uniqueID)
                self.Scrape(doc, uniqueID)  # UNCOMMENT!!!!!!!!
                self.i += 1

    '''
    The function will create a directory to hold the xlsx file generated for all pdfs analyzed if doesn't already
    exist. If a previous xlsx file was generated it is appended to with the newly analyzed pdfs, but if no xlsx exists
    then it will generate an xlsx with the proper row and column format.
    '''

    # APPEND FEATURE NOT TESTED
    def WritetoXLSX(self):
        rownames = ['sequenceno', 'clin_history', 'final diagnosis',
                    'pathologist', 'lm_results', 'em_results', 'if_results']
        self.DestroyPatch()

        # append to existing xlsx (UNTESTED)
        if(os.path.exists('xlsxfiles/AINBankrepo.xlsx')):
            for i, data in enumerate(self.docsdata):
                data.insert(0, self.docsread[i])

            biopsydf = pd.DataFrame(self.docsdata, index=self.docsread, columns=rownames)

            with pd.ExcelWriter('xlsxfiles/biobankrepo.xlsx', mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                biopsydf.to_excel(writer, sheet_name='AINbank scraped pdfs', header=None,
                                  startrow=writer.sheets["AINbank scraped pdfs"].max_row, index=False)
            return

        # if the xlsx sheet doesn't exist (ideally one time use)
        else:
            try:
                os.mkdir('xlsxfiles')
            except:
                pass

            for i, data in enumerate(self.docsdata):
                data.insert(0, self.docsread[i])

            biopsydf = pd.DataFrame(self.docsdata, index=self.docsread, columns=rownames)
            biopsydf.to_excel('xlsxfiles/AINBankrepo.xlsx', sheet_name='AINbank scraped pdfs')
            return

    # testing append to xlsx feature
    # def test_append_xlsx(self):
    #     biopsydf = pd.read_excel('xlsxfiles/biobankrepo.xlsx')
    #     with pd.ExcelWriter('xlsxfiles/testwrite.xlsx', mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
    #         biopsydf.to_excel(writer, sheet_name='Sheet1', header=None, startrow=writer.sheets["Sheet1"].max_row, index=False)

    # NOT TESTED
    '''
    Moves unprocessed pdfs to the processed file collection using the paths attributes
    '''

    def MoveFromStaging(self):
        try:
            self.CreatePatch()
        except Exception as e:
            print(e)

        try:
            os.mkdir('Pathology Report PDF Analyzed')
        except:
            pass

        for doc in os.listdir(os.getcwd()):
            os.rename('{}/{}'.format(self.drivepath, doc), '{}/{}'.format(self.procesedpath, doc))

    # NOT TESTED - DELETES BOX TIFFS and TIFF transition files
    def CleanUp(self):
        self.DestroyPatch()

        try:  # destroy textbox tiffs
            os.rmdir('TEXTBOX_tiffs')
        except OSError as e:
            print('Error: {} : {}'.format('TEXTBOX_tiffs', e.strerror))

        try:  # destory transition .tiff files
            os.rmdir('TIFFS')
        except OSError as e:
            print('Error: {} : {}'.format('TIFFS', e.strerror))

    # future db solution to replace xlsx file solution

    def Create_DB_connection(self, db_file):
        try:
            os.mkdir('sqlite')
        except:
            pass
        try:
            os.mkdir('sqlite/db')
        except:
            pass

        conn = None
        try:
            conn = sqlite3.connect(db_file)
            print(sqlite3.version)

        except Error as e:
            print('DB connection error {}'.format(e))

        self.dbconnection = conn


def main():
    Drive = ScrapeDriver()
    Drive.PullFiles()  # load files into pdfs attribute, WORKS
    Drive.AnalyzePdfs()  # generates the uniqueID and feeds to the Scrape function WORKS

    print('\n\n\t\t SUMMARY: number of docs read = ({}) == ({})\n\n'.format(len(Drive.docsdata), Drive.i))
    Drive.WritetoXLSX()
    print('Wrote out to xlsx files')

    for key, value in Drive.error:
        print(value)
    done = input("Done with Error Output: \n?> ")
    if(done.lower() in ['y', 'yes']):
        return

    # Drive.CleanUp()

    # Drive.Create_DB_connection('sqlite/db/BioBank.db')
    # counter = 0

    # print('#doc = {}'.format(Drive.i))
    # userin = input("ready for error output?\n?>")
    # if(userin.lower() in ['y', 'yes']):
    #     for key, value in Drive.error.items():
    #         print(value)


main()
