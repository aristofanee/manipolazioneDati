import os
from tkinter.filedialog import askdirectory
from tkinter import Tk
import functions
import shutil
import numpy as np
import pandas as pd

root = Tk()
root.withdraw()

warningMode = 'auto'
invalidCharacters = ['?', '�', '[',']', '⁻', chr(8314)]
invalidHeaderCharacters = ['_', '(', ')', '.', '/']

sourceFolder = askdirectory(title="Select the folder.")
parentFolder = os.path.dirname(sourceFolder)
folderName = os.path.basename(sourceFolder)

cleanFolderName = functions.removeCharacters(folderName, invalidCharacters)

cleanFolderName = cleanFolderName + "_manipulated"

print("Copying files...")
manipulatedFolder = os.path.join(parentFolder,cleanFolderName)
shutil.copytree(sourceFolder, manipulatedFolder, dirs_exist_ok=True)
print("All files have been copied.\n")

for root, dirs, files in os.walk(manipulatedFolder, topdown=False):
    for file in files:
        if file.endswith(".txt") and "Current" in file:
            fullPath = os.path.join(root, file)
            os.remove(fullPath)

    for dir in dirs:
        newDirName = functions.removeCharacters(dir, invalidCharacters)
        fullPath = os.path.join(root, dir)
        fullRenamePath = os.path.join(root, newDirName)

        os.rename(fullPath, fullRenamePath)

txtFiles: list[str] = [] 
for root, dirs, files in os.walk(manipulatedFolder, topdown=False):
    for file in files:
        if file.endswith(".txt"):
            fullPath = os.path.join(root, file)
            txtFiles.append(fullPath)

nTests = len(txtFiles)
failedFiles: list[(str, Exception)] = []

# Start of the main loop
for test in txtFiles:
    folderTest = os.path.dirname(test)
    relativePath = test.replace(manipulatedFolder, '')


    # Check if the txt file is a test
    if not functions.testCheck(test):
        print(relativePath + " was not a test.")
        os.remove(test)
        continue

    # Start of the exeption handling
    try:
        with open(test,"r") as file:
            fileContent = file.readlines()

        descriptionLines = fileContent[:2]
        columnNames = fileContent[2].strip().split('\t')
        unitsOfMeasure = fileContent[3].strip().split('\t')

        columnNames = [functions.removeCharacters(header, invalidHeaderCharacters) for header in columnNames]
        
        #print(columnNames)

        table = pd.read_csv(test, skiprows=2, header=0, encoding="cp1252")

        table.columns = [functions.removeCharacters(header, invalidHeaderCharacters) for header in table.columns]
        table.columns = [functions.removeSpaceCaps(header) for header in table.columns]

    except Exception as e:
        failedFiles.append((relativePath, e))
        errorMessage = "There was an error: " + str(e) + "\n"
        errorMessage = errorMessage + relativePath + " was NOT processed"
        functions.decorateSentence(errorMessage, True)
        




if failedFiles:
    # TODO
    print(len(failedFiles))
    print("there are some failed files") 