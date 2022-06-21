# KUH 2022: BioBank PDF Scraper & NLP analysis 
--------------------------------------------------------------------------------
![Python application](https://github.com/stephenbaek/imagiqfl/workflows/Python%20application/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This repository houses the ScrapeDriver developed for the Yale University School of Medicine's BioBank project and the associated NLP algorithim. The goals for the ScrapeDriver and NLP alogrithim used in tandem are:

- Offer accurate, efficient, and scalable text-scraping of Yale NewHaven Health Pathology pdf reports.
- Convert "dirty" data into usable medically relevant data that allows for the testing for the presence of statistically significant biological trends.
- Offer an alternative to current labor intensive scraping and analysis techniques.

The Yale University School of Medicine's KUH program is funded by the NIH
<p align="center">
  <img src="https://www.lifespan.io/wp-content/uploads/2020/06/Yale-School-of-Medicine.png" alt='imagiq-logo'>
</p>

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
#### 5) pdf2image (specifically the "convert_from_path" function)
The `pdf2image` package is a efficient pdf to image converter that allows for conversion to most popular image extensions. .tiff format works best for `pytesseract` and .tiff conversions is a strength of `pdf2image`. 

```
conda install -c conda-forge pdf2image
```
OR
```
pip install pdf2image
```
When installing the `pdf2image` package the conda installation is always preferred, but the secondary pip installtion is provided if an `ImportError` arises. This error and solving it will be discussed later.

#### 5.5) poppler
The `poppler` package is an necessary python binding to the `poppler-cpp` (poppler C++) library. This library grants the ability to read, render, and modify pdf documents. While this project does make use of these features, the `pdf2image` package requires a linking between the 2 to function properly. This linking will be discussed later.
```
brew install poppler
```
OR
```
conda install -c conda-forge poppler
```
While it is reccomended to use the conda installation when using conda environments, I have had `ImportErrors` when installing the poppler package through conda due to unsucessful linking mentioned earlier. 
#### 5.55) Errors with pdf2image and poppler
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


# The Team
This repo is currently maintained by [Anshul Gowda](https://www.linkedin.com/in/anshul-gowda-693206200/). Feel free to reach out!

# Citation
This repo is free for an academic use. Please do not forget to cite the following paper.

# License
TODO: Define a license. 
