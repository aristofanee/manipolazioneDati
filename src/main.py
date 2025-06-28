import os
from tkinter.filedialog import askdirectory
from tkinter import Tk
import functions
import shutil

root = Tk()
root.withdraw()

warningMode = 'auto'

sourceFolder = askdirectory(title="Select the folder.")
parentFolder = os.path.dirname(sourceFolder)
folderName = os.path.basename(sourceFolder)

cleanFolderName = functions.removeCharacters(folderName)

cleanFolderName = cleanFolderName + "_manipulated"

print("Copying files...")
manipulatedFolder = os.path.join(parentFolder,cleanFolderName)
shutil.copytree(sourceFolder, manipulatedFolder, dirs_exist_ok=True)
print("All files have been copied.\n")

for root, dirs, files in os.walk(manipulatedFolder, topdown=False):
    for file in files:
        if file.endswith(".txt") and "current" in file:
            fullPath = os.path.join(root, file)
            os.remove(fullPath)

    for dir in dirs:
        newDirName = functions.removeCharacters(dir)
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
failedFiles = []

# Start of the main loop
for test in txtFiles:
    folderTest = os.path.dirname(test)
    relativePath = test.replace(manipulatedFolder, '')


    # Check if the txt file is a test
    if not functions.testCheck(test):
        print(relativePath + " was not a test.")
        os.remove(test)
        continue

    try:
        raise ValueError('A very specific bad thing happened.')
    except Exception as e:
        failedFiles.append(relativePath)
        errorMessage = "There was an error: " + str(e) + "\n"
        errorMessage = errorMessage + relativePath + " was NOT processed"
        functions.decorateSentence(errorMessage, True)



