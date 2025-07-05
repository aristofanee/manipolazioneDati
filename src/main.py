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
failedFiles: list[tuple[str, Exception]] = []

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
        unitsOfMeasure = fileContent[3]

        # Importing the csv into a pandas table
        table = pd.read_csv(test, skiprows=[0,1,3], header=0, encoding="cp1252", delimiter='\t')
        table = table[table.apply(functions.isRowAllFloat, axis=1)].reset_index(drop=True)
        table = table.astype('float')
        # print(table['TimeToCollisionLongitudinal'])
        # Edit the name of the headers to match the Matlab ones TODO
        table.columns = [functions.removeCharacters(header, invalidHeaderCharacters) for header in table.columns]
        table.columns = [functions.removeSpaceCaps(header) for header in table.columns]

        (isLSS, LSSDirection) = functions.LSSCheck(test)

        table['RelativeLateralDistance'] = table['RelativeLateralDistance'] * -1


        (newTime, startTestIndex) = functions.TTCProcess(
            table['TimeToCollisionLongitudinal'],
            table['Time'], isLSS)

        header = descriptionLines
        header.append(unitsOfMeasure)
        functions.exportFile(test, table, header)






    #except Exception as e:
    except ValueError as e:
        failedFiles.append((relativePath, e))
        errorMessage = "There was an error: " + str(e) + "\n"
        errorMessage = errorMessage + relativePath + " was NOT processed"
        functions.decorateSentence(errorMessage, True)


if failedFiles:
    # TODO implement the real output log
    print("There are", len(failedFiles),  "failed files")
