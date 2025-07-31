import os
import shutil
import functions
from io import StringIO

# Main function
def main():
    # Configuration
    warningMode = 'auto'
    adc6Name = 'ADC6'
    invalidCharacters = ['?', '�', '[', ']', '⁻', chr(8314)]
    invalidHeaderCharacters = ['_', '(', ')', '.', '/']

    # Get source folder with lazy GUI import
    sourceFolder = functions.getFolder()
    if not sourceFolder:
        return

    # Setup folders
    parentFolder = os.path.dirname(sourceFolder)
    folderName = os.path.basename(sourceFolder)

    cleanFolderName = functions.removeCharacters(folderName, invalidCharacters)
    cleanFolderName = cleanFolderName + "_manipulated"

    print("Copying files...")
    manipulatedFolder = os.path.join(parentFolder, cleanFolderName)
    shutil.copytree(sourceFolder, manipulatedFolder, dirs_exist_ok=True)
    print("All files have been copied.\n")

    # Clean up files and directories
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

    # Find all txt files
    txtFiles: list[str] = []
    for root, dirs, files in os.walk(manipulatedFolder):
        for file in files:
            if file.endswith(".txt"):
                fullPath = os.path.join(root, file)
                txtFiles.append(fullPath)

    nTests = len(txtFiles)
    failedFiles: list[tuple[str, Exception]] = []
    currentTestCount = 0

    pd = functions.loadPandas()
    print("Found", nTests, "test files to process.")

    # Start of the main loop
    for test in txtFiles:
        currentTestCount += 1
        folderTest = os.path.dirname(test)
        relativePath = test.replace(manipulatedFolder, '')

        # Check if the txt file is a test
        if not functions.testCheck(test):
            print(relativePath + " was not a test.")
            os.remove(test)
            continue

        # Start of the exception handling
        try:
            with open(test, "r") as file:
                fileContent = file.readlines()

            descriptionLines = fileContent[:2]
            numberDataRows = int(descriptionLines[1].split("=")[1].strip())
            totalLines = len(fileContent)
            unitsOfMeasure = fileContent[3]

            headerLines = descriptionLines
            headerLines.append(unitsOfMeasure)

            # Importing the csv into a pandas table
            rowsSkipped = [0, 1, 3] + list(range(4 + numberDataRows, totalLines))

            data = StringIO(''.join(fileContent))
            table = pd.read_csv(data, skiprows=rowsSkipped, header=0, encoding="cp1252", delimiter='\t', dtype=float)

            # Edit the name of the headers to match the Matlab
            table.columns = [functions.removeCharacters(header, invalidHeaderCharacters) for header in table.columns]
            table.columns = [functions.removeSpaceCaps(header) for header in table.columns]

            numberOfColumns = len(table.columns)


            (isLSS, LSSDirection) = functions.LSSCheck(test)

            table['RelativeLateralDistance'] = table['RelativeLateralDistance'] * -1

            (newTime, startTestIndex) = functions.TTCProcess(
                table['TimeToCollisionLongitudinal'].copy(),
                table['Time'].copy(), isLSS)

            if 'ADC6' not in table.columns:
                indexADC5 = list(table.columns).index('ADC5')
                newColumnNames = list(table.columns)
                newColumnNames[indexADC5 + 1] = 'ADC6'
                table.columns = newColumnNames

            table['ADC6'] = functions.warningProcess(table['ADC6'].copy(), isLSS, newTime, startTestIndex, warningMode)

            if isLSS:
                dt = table['Time'][1] - table['Time'][0]
                approachSpeed, distToLine = functions.LSSProcessing(test, dt, table["ActualYFrontAxle"].copy(), LSSDirection)
                table['ApproachSpeed'] = approachSpeed
                table['DistToLine'] = distToLine
                headerLines[2] = functions.addUnitToLSS(len(table.columns), headerLines[2])


            table = table.rename(columns = {'TimeToCollisionLongitudinal':'TimeToCollisionlongitudinal'})

            functions.exportFile(test, table, headerLines)

            currentPercentage = currentTestCount / nTests * 100
            formattedPercentage = f"{currentPercentage:.2f}%"
            print(formattedPercentage, "\t", relativePath, "was processed.")

        except Exception as e:
            failedFiles.append((relativePath, e))
            errorMessage = "There was an error: " + str(e) + "\n"
            errorMessage = errorMessage + relativePath + " was NOT processed"
            functions.decorateSentence(errorMessage, True)

    # Write error log if there were failures
    if len(failedFiles) != 0:
        with open(os.path.join(parentFolder, "error_" + folderName + ".log"), 'w') as file:
            for errorPath, error in failedFiles:
                file.write("Error: " + str(error) + " File: " + errorPath + "\n")








# Tells the script to start with the main function
if __name__ == "__main__":
    main()
