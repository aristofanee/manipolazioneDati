from colorama import init, Fore, Style
from enum import Enum
import os

# Function to load pandas when needed
def loadPandas():
    import pandas as pd
    return pd
# Function to open the dialog box for selecting the folder
def getFolder():
    from tkinter.filedialog import askdirectory
    from tkinter import Tk

    root = Tk()
    root.withdraw()

    sourceFolder = askdirectory(title="Select the folder.")

    if not sourceFolder:
        print("No folder was selected.")
        return None

    return sourceFolder

 # Simplify the removal of characters
def removeCharacters(genericString: str, charList: list[str]) -> str:
    cleanString = genericString
    for characters in charList:
        cleanString = cleanString.replace(characters, '')
    return cleanString

# Check if the .txt file has also a .spec file in the same folder
def testCheck(test: str) -> bool:
    testFolder = os.path.dirname(test)
    specPath = test.replace(".txt", ".spec")
    return os.path.exists(specPath)

# Just to print error messages with more enphasis
def decorateSentence(sentence: str, isRed: bool):
    init()
    if isRed:
        print(Fore.RED)
    print("---------------------------------------------------------------------------------")
    print(sentence)
    print("---------------------------------------------------------------------------------")
    print(Style.RESET_ALL)

# Manually refactoring the header names according to the MATLAB notation
def removeSpaceCaps(genericString: str) -> str:
    outputString: list[str] = []
    spacePresent = False

    for index, char in enumerate(genericString):
        if char == ' ':
            spacePresent = True
        else:
            if spacePresent and char.isalpha():
                outputString.append(char.upper())
                spacePresent = False
            else:
                outputString.append(char)

    return ''.join(outputString)

# Enum for LSS direction, non used yet
class Direction(Enum):
    RIGHT = object()
    LEFT = object()
    NONE = object()

# Check if the test is an LSS test and finds the direction of the manover from the .spec file
def LSSCheck(test: str) -> tuple[tuple[bool,bool], Direction]:
    specTest = test.replace(".txt", ".spec")

    LSSIdentifiers = ('LKA','ELK','LDW')
    rightIdentifiers = ('Right', 'Road')
    leftIdentifiers = ('Left', 'Over', 'Onc', 'CMOv')
    OncOverIndentifiers = ('Over', 'Onc', 'CMOv')

    with open(specTest, "r") as specFile:
        specContent = specFile.readlines()

    descriptionLine = specContent[1]
    isJustLSS = any(identifier in descriptionLine for identifier in LSSIdentifiers)
    isOncOver = any(identifier in descriptionLine for identifier in OncOverIndentifiers) and 'NVT' not in descriptionLine

    if isJustLSS:
        if any(identifier in descriptionLine for identifier in rightIdentifiers):
            LSSdirection = Direction.RIGHT
        elif any(identifier in descriptionLine for identifier in leftIdentifiers):
            LSSdirection = Direction.LEFT
        else:
            raise RuntimeError("No direction was found in the .spec file for the LSS scenario.")
    else:
        LSSdirection = Direction.NONE
        descriptionLine = descriptionLine.replace(" kph", "VUT")
        specContent[1] = descriptionLine

        with open(specTest, "w") as specFile:
            specFile.writelines(specContent)

    return ((isJustLSS,isOncOver), LSSdirection)

# Process the TTC
def TTCProcess(TTCVector, TimeVector, isLSS):

    if (isLSS[0] and not isLSS[1]) or (TTCVector == 0).all():
        newTime = None
        startTimeIndex = None
        return (newTime, startTimeIndex)

    # Lazy import numpy only when needed
    import numpy as np

    index = 0

    # The loop tries to fill holes in the TTC columns where the TTC is 0
    while index < len(TTCVector) or not index:
        if TTCVector[0] == 0:
            index = TTCVector[TTCVector > 0].index.tolist()[0]
            TTCVector[0:index] = TTCVector[index]
            index = 0

        index = TTCVector[TTCVector == 0].index.tolist()

        if len(index) == 0:
            break
        else:
            index = index[0]

        yStart = (TTCVector[index - 1], index - 1)
        index = TTCVector[index:][TTCVector > 0].index.tolist()

        if len(index) == 0:
            startTestIndex = 0
            break
        else:
            index = index[0]

        yEnd = (TTCVector[index], index)
        xEq = np.arange(0, yEnd[1] - yStart[1])
        m = (yEnd[0] - yStart[0]) / (yEnd[1] - yStart[1])
        TTCEq = m*xEq + yStart[0]
        TTCVector[yStart[1]:yEnd[1]] = TTCEq

    # Shifts the Time frame to start at TTC 4
    startTestIndex = TTCVector[TTCVector < 4].index.tolist()

    if len(startTestIndex) == 0:
        startTestIndex = 0
    else:
        startTestIndex = startTestIndex[0]

    newTime = TimeVector[startTestIndex:] - 4 - TimeVector[startTestIndex]

    return(newTime, startTestIndex)

# Check if all the items in a collection are Floats, non needed anymore with the new import
def isRowAllFloat(row):
    try:
        [float(x) for x in row]
        return True
    except ValueError:
        return False

# Finds were the ADC6 changes from HIGH to a threshold and then creates a step function
# where the warning is 0 before and 5 after
def warningProcess(ADC6Vector, isLSS, newTime, startTestIndex, warningMode):
    ADC6Out = ADC6Vector.copy()
    ADC6Out[:] = 0

    if (isLSS[0] and not isLSS[1]) or startTestIndex == None:
        return ADC6Out

    warningThreshhold = 1

    match warningMode:
        case 'auto':
            dY = ADC6Vector.diff()
            dY[0] = dY[1]
            dY = dY.abs()
            indexFirstWarning = dY.iloc[startTestIndex:][dY.iloc[startTestIndex:] > warningThreshhold].index.tolist()
        case _:
            dY = ADC6Vector.diff()
            dY[0] = dY[1]
            dY = dY.abs()
            indexFirstWarning = dY.iloc[startTestIndex:][dY.iloc[startTestIndex:] > warningThreshhold].index.tolist()

    if len(indexFirstWarning) != 0:
        ADC6Out[startTestIndex + indexFirstWarning[0]:] = 5

    return ADC6Out

# Process the LSS to add the lateral velocity column and the distance from the line
def LSSProcessing(test, dt: float, positionVector, LSSDirection, isOncOver):
    # Lazy import scipy only when needed for LSS processing
    from scipy import signal

    parentFolder = os.path.dirname(test)
    lineFolder = os.path.dirname(parentFolder)

    if not isOncOver:
        zeroFile = os.path.join(lineFolder, "zero.ini")

        if not os.path.isfile(zeroFile):
            raise Exception("No zero.ini file was found.")

        with open(zeroFile, 'r') as file:
            zero = file.readline()
        zero = float(zero)
    else:
        zero = 0

    distToLine = positionVector - zero

    Wn = 10/50
    sos = signal.butter(6, Wn, btype='low', output='sos')

    derivPosition = positionVector.diff() / dt
    derivPosition[0] = derivPosition[1]  # Removes the NaN as the first element from the vector

    derivPosition = signal.sosfiltfilt(sos, derivPosition)

    return (derivPosition, distToLine)

# Needed for LSS scenarios to be correctly processed in X-Zero
# adds the units of measure to the two columns created for the LSS scenarios
def addUnitToLSS(numberOfHeaders, unitOfMeasureHeader):
    numberUnitOfMeasure = unitOfMeasureHeader.count('\t')
    unitOfMeasureHeader = unitOfMeasureHeader.strip()

    for i in range(numberOfHeaders - numberUnitOfMeasure - 2):
        unitOfMeasureHeader = unitOfMeasureHeader + '\t'


    unitOfMeasureHeader = unitOfMeasureHeader + '\tm/s\tm\n'
    return unitOfMeasureHeader

# Exports the table to the .txt file. The encoding and the newline parameters are crucial
# for the files to be imported in X-Zero
def exportFile(testFile, table, headers: list[str]):
    with open(testFile, 'w', newline='\r\n', encoding="cp1252") as file:
        file.write(headers[0])
        file.write(headers[1])
        file.write('\t'.join(table.columns) + "\n")
        file.write(headers[2])

    with open(testFile, 'a', newline='', encoding="cp1252") as file:
        table.to_csv(file, sep="\t", index=False, header=False, lineterminator = '\r\n')
