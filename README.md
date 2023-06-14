# KUH 2022: BioBank PDF Scraper & ML Clinical Feature Extraction
![Python Application](https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1869px-Python-logo-notext.svg.png)
![Python application](https://github.com/stephenbaek/imagiqfl/workflows/Python%20application/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
--------------------------------------------------------------------------------
<p float="center">
  <img src="https://www.lifespan.io/wp-content/uploads/2020/06/Yale-School-of-Medicine.png" width="350" height="215"alt='YaleSoM logo'/>
  <img src="https://ysm-res.cloudinary.com/image/upload/c_limit,f_auto,h_630,q_auto,w_1200/v1/yms/prod/4ab3b4a4-a6aa-40a0-99eb-1118be087ddd" width="350" height="215"alt="CTRA logo"/> 
</p>

--------------------------------------------------------------------------------

This repository houses the ScrapeDriver developed for the Yale University School of Medicine's BioBank project through CTRA (Clinical and Translational Research Accelerator) and the associated NLP algorithim. The goals for the ScrapeDriver and NLP alogrithim used in tandem are to :

- Offer accurate, efficient, and scalable text-scraping of Yale NewHaven Health Kidney Biopsy Pathology pdf reports.
- Converts unstructured data into semi-structured medically relevant data, that allows for academic analysis for the presence of statistically significant biological trends.
- Offer an alternative to current manual extraction techniques and reassessment by pathologists/medical providers.

The Yale University School of Medicine's KUH program is funded by the NIH

# ML Based Clinical Feature Extractor
Scraping the histological and clinically relevant data off of kindey biopsy reports returns key qualitative data. This qualitative data is not suited for industry and academic standard statistical and algorithmic analyses. Thus, with the help of Aditya Biswas MS, data scientist, we are implementing a model based clinical feature extraction pipeline to extract standard factors from variably structured clinical data produced by the Scrape Engine. Currently we are training and optimizing binary prediction models to predict the presence of specific conditions, specifically these models extract:
- Crescents
- Tubulitis
- Focal Glomerulosclerosis

We are hope to further train these models or combine them with Natural Language Processing's (NLP) Named Entity Recognition (NER) to pull out the numeric quantifiers associated with these conditions; these include number, relative percentage, ratios, etc. The extraction of numeric quantifiers will fully convert this semi-structured qualitative data into structured quantitative data including accurate standard clinical factors. 

# Getting Started
## Installation
### Using Anaconda/Miniconda
Probably the simplest way to get started is by using [Conda](https://en.wikipedia.org/wiki/Conda_(package_manager)), which can be downloaded from https://www.anaconda.com/products/individual. Installing Conda should be fairly straightforward, with lots of tutorials and blog posts you can find on the internet (such as [this](https://www.youtube.com/watch?v=YJC6ldI3hWk&ab_channel=CoreySchafer)).

Once Conda has been properly installed, you should be able to run the following command in terminal/command prompt to create a virtual environment:
```
conda create --name BioBankScraper python=3.8
```
Note that `BioBankScraper` is the name of the environment to be created and `python=3.8` specifies a Python version for the environment. The Repo has been coded and tested using version 3.8 but should be usable until 3.5.

After the new environment is created, activate it by typing:
```
conda activate BioBankScraper
```
Once the environemnt is activated you will have access to the base packages through Anaconda and can install project specific packages, which we will talk about soon. To exit out of the environment type:
```
conda deactivate BioBankScraper
```

### Dependent Packages
Next is to install the dependent packages (each with their own relevant dependencies, which Conda will take care off):
#### 1) Opencv or cv2
The `cv2` package is an extremely popular and nuanced Computer Vision Open Source Python library. For this project `cv2` is mainly used for the file mainpulation features that are not available or easily usable using the `os` module. 
```
conda install -c conda-forge opencv
```
#### 2) pytesseract 
The `pytesseract` package is a wrapper for `Google’s Tesseract-OCR Engine`. This package is able to read and recognize text from image files using ML script. In this project it is used to scrape text from the .tiff files generated from the .pdfs reports in the BioBank
```
conda install -c conda-forge pytesseract
```
#### 3) pandas
The `pandas` library is a statistical and data structure python library. It allows for users to build complex relational data structures and has the ability for real-time complex statistical analysis, quantification, and dynamic representations. For this project, Pandas is used to organize the data returned from text-scraping of the pdfs before it is output to xlsx/database.
```
conda install -c anaconda pandas
```
#### 4) openpyxl
The `openpyxl` package is a common and reliable engine used for read-in and write-out data streams. It is a commonly required dependency for projects that have heavy input/output flows as this project does. 
```
conda install -c anaconda openpyxl
```
#### 5) Git
`Git` is version-control system that allows developers to track changes in their code and to facilitate code collaboration. Specifically, we will use `Git` to create a local copy of the source code that you can run. If wanted Git can be used to save changes you make in the source code and can be stored in a remote Repository in GitHub which I will elaborate on next.

To download Git type:
```
conda install -c anaconda git
```
#### 5.5) GitHub
`GitHub` is an industry standard remote repository where developers save their code and facilitate collaboration on Open Source projects. Storing your code in GitHub is optional but it is highly reccomended. To make a GitHub account [CLICK HERE](https://github.com/join)

#### 6) scispacy
`scispacy` is a python package that contains spacy models that are aimed to provide deep-learning for clinical, biomedical, and biological text. One of the most important features of `scispacy` is its `Named Entity Recognition (NER)` feature, which is able to identify medicaly relevant "entities" within the text. To install scispacy:
```
pip install scispacy
```
#### 6.5) scispacy trained model
`scispacy` comes with many pre-trained modesl that are trained on different collections of medical text that are geared towards different specialities of the medical field. These models are listed [HERE](https://allenai.github.io/scispacy/).
We will be using the (middle or larger) sized model. To instal this model in your environment, type:
```
pip install {link to the model}
```
for example if downloading the middle sized model, the command would be:
```
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.0/en_core_sci_md-0.5.0.tar.gz
```

#### 7) negspacy
'

#### 8) pdf2image (specifically the "convert_from_path" function)
The `pdf2image` package is a efficient pdf to image converter that allows for conversion to most popular image extensions. .tiff format works best for `pytesseract` and .tiff conversions is a strength of `pdf2image`. 

```
conda install -c conda-forge pdf2image
```
OR
```
pip install pdf2image
```
When installing the `pdf2image` package the conda installation is always preferred, but the secondary pip installtion is provided if an `ImportError` arises. This error and solving it will be discussed later.

#### 8.5) poppler
The `poppler` package is an necessary python binding to the `poppler-cpp` (poppler C++) library. This library grants the ability to read, render, and modify pdf documents. While this project does make use of these features, the `pdf2image` package requires a linking between the 2 to function properly. This linking will be discussed later.
```
brew install poppler
```
OR
```
conda install -c conda-forge poppler
```
While it is reccomended to use the conda installation when using conda environments, I have had `ImportErrors` when installing the poppler package through conda due to unsucessful linking mentioned earlier. 
#### 8.55) Errors with pdf2image and poppler
When setting up both the `pdf2image` and `poppler` binding I have had multiple set up issues. Specifically there is a very common `ImportError` that arises:
```
Traceback (most recent call last):
  File "ScrapeDriver.py", line 1, in <module>
    from pdf2image import convert_from_path
ImportError: No module named pdf2image
```
However, if you have followed this guide and installed pdf2image correctly this should not happen since you have already installed `pdf2image` and it should be recognized. To double check that you have installed the required packages use this command after you have activated your conda env:
```
conda list
```
This command should list all the packages installed in your current conda environment. If the `pdf2image` package is present in this list but you still get the specific `ImportError` then there is an issue between the `pdf2image` and `poppler` linking. To fix this you must make sure `poppler` is installed by using the previous command. If it is installed and still returning an `ImportError` then you must try using `brew` to install then reinstall `poppler` which will erase the previous linking
```
brew install poppler
```
```
brew reinstall poppler
```
This should fix the problem, but if this issue still exists then there is most likley a complex path routing issue between these two packages. `brew` may ask you to manually link `poppler` and `pdf2image` and if it does follow the instructions and specific command prompts it provides.

### Using VirtualEnv
TODO: Add a description here.

### Local Routing/Directory Setup
#### Connecting to the Shared Drive
The BioBank is a remote directory stored in Shared Drive that is hosted by the Yale University Servers. To connect to the server hosting the ShareDrive you must either be connected to YaleSecure WiFi or establish a connection through `Cisco AnyConnect Secure Mobility Client`.

#### (MAC OS) Accessing the Shared Drive
To access the Shared Drive you must establish a connection to the Yale Server through the `Finder` application. In `Finder` select the `Go` tab and navigate to the `Connect to Server` option in the dropdown menu. It will prompt you to enter the address to the remote server. Enter:
```
smb://storage.yale.edu/home/MoledinaLab-CC1032-MEDINT
```
Once a secure connection is established you now have access to the full Shared Drive.

#### (MAC OS) Accessing the BioBank
To access the BioBank directories containing all of the PDF Biopsy Reports. In Mac OS the Shared Drive is stored in the `Volumes` directory in the `root` directory. There are two directories containing the PDF Biopsy Reports:
```
/Volumes/MoledinaLab-CC1032-MEDINT/Biobank 27890/Pathology Report PDF Staging
```
AND
```
/Volumes/MoledinaLab-CC1032-MEDINT/Biobank 27890/Pathology Report PDF Analyzed
```
The `Staging` directory contains the Biopsy Reports that have not been scraped by the script, and the `Analyzed` directory contains the Biopsy Reports that have been sucessfully scraped. The movement of files from the `Staging` to the `Analyzed` directory is handled by the script.

#### Setting up a Local Project
To use this script locally, you must first make a copy of the source code stored here in the `KUH 2022` repository. However, you must first make a local directory to house the source code. Make sure to note down the full path of this directory. Once you have made this directory navigate to this directory in your terminal and clone the source code using this command:
```
git clone https://github.com/anshuljg07/KUH2022.git
```
This should have populated the newly made directory with the soure code files from the `KUH 2022` repository.

#### Setting up Routing in ScrapeDriver.py
The ScrapeDriver.py file was configured to work on Anshul's local machine, so it needs to be configured to work on your machine. To do this locate the attribute `homepath` located on line 16. It should look like this:
```
self.homepath = '/Users/anshulgowda/Documents/CODE/KUH2022/'
```
Set this variable to the directory you created that houses the cloned source code. Line 17 should now look like this:
```
self.homepath = {YOUR PATH GOES HERE}
```
Furthermore, you need to change where the script goes to search for the biopsy files that will be scraped. To do this locate the attribute `drivepath` and change it to the path of the directory where the biopsy pdfs, or the staging directory. Line 16 should look like this:
```
self.drivepath = {YOUR PATH GOES HERE}
```
Lastly, you need to specify where the script should move the files after they have been scripted. To do this locate the attribute `processedpath` and change it to the path of an empty directory that you have created. Line 15 should look like this:
```
self.processedpath = {YOUR PATH GOES HERE}
```




ScrapeDriver.py will automatically access the shared drive where the 


# The Team
This repo is currently maintained by [Anshul Gowda](https://www.linkedin.com/in/anshul-gowda-693206200/) and Aditya Biswas. Feel free to reach out!

# Citation
This repo is free for an academic use. Please do not forget to cite the following paper.

# License
TODO: Define a license. 
