import os


class DrivePatch:
    def __init__(self):
        self.drivepath = '/Volumes/MoledinaLab-CC1032-MEDINT/Biobank 27890/Pathology Report PDF/'
        self.homepath = '/Users/anshulgowda/Documents/CODE/KUH2022/'

    def CreatePatch(self):
        try:
            os.chdir(self.drivepath)
            print('working directory changed to:\t{}'.format(os.getcwd()))
            return True
        except OSError:
            print('unable to connect to share drive ({})\ncurrent working directory: {}'.format(
                self.drivepath, os.getcwd()))
            return False

    def DestroyPath(self):
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
            pass


def main():
    print('working directory: {}'.format(os.getcwd()))
    # os.chdir('/Volumes/MoledinaLab-CC1032-MEDINT/Biobank 27890/Pathology Report PDF/')
    os.chdir('/Users/anshulgowda/Documents/CODE/KUH2022/')
    print('working directory: {}'.format(os.getcwd()))

    for filename in os.listdir(os.getcwd()):
        # call the read pdf funcs in "jpegtotext.py" prolly need to rename the file to
        # "biopsyscraper.py"


main()
