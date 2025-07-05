from colorama import init, Fore, Style
from enum import Enum
import numpy as np
import pandas as pd
import os
import plotly.express as px
from scipy import signal

def removeCharacters(genericString: str, charList: list[str]) -> str:

    cleanString = genericString

    for characters in charList:
        cleanString = cleanString.replace(characters, '')

    return cleanString

def testCheck(test: str) -> bool:
    testFolder = os.path.dirname(test)
    specPath = test.replace(".txt", ".spec")
    return os.path.exists(specPath)

def decorateSentence(sentence: str, isRed: bool):
    init()
    if isRed:
        print(Fore.RED)
    print("---------------------------------------------------------------------------------")
    print(sentence)
    print("---------------------------------------------------------------------------------")
    print(Style.RESET_ALL)


def removeSpaceCaps(genericString: str) -> str:
    outputString:list[str] = []
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

class Direction(Enum):
    RIGHT = object()
    LEFT = object()
    NONE = object()

def LSSCheck(test:str) -> tuple[bool, Direction]:
    specTest = test.replace(".txt", ".spec")

    LSSIdentifiers = ('LKA','ELK','LDW')

    rightIdentifiers = ('Right', 'Road')
    leftIdentifiers = ('Left', 'Over', 'Onc', 'CMOv')

    with open(specTest, "r") as specFile:
        specContent = specFile.readlines()

    descriptionLine = specContent[1]

    isLSS = any(identifier in descriptionLine for identifier in LSSIdentifiers)

    if isLSS:
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

    return (isLSS, LSSdirection)

def TTCProcess(TTCVector, TimeVector, isLSS):

    if isLSS or (TTCVector == 0).all():
        newTime = None
        startTimeIndex = None
        return (newTime, startTimeIndex)

    index = 0

    while index < len(TTCVector) or not index:


        if TTCVector[0] == 0:
            #TTCVector = TTCVector.copy()
            index = TTCVector[TTCVector > 0].index.tolist()[0]
            print("this is the index:" , index)
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


    startTestIndex = TTCVector[TTCVector < 4].index.tolist()

    # TODO Check with a real test with a working TTC
    if len(startTestIndex) == 0:
        startTestIndex = 0
    else:
        startTestIndex = startTestIndex[0]

    newTime = TimeVector[startTestIndex:] - 4 - TimeVector[startTestIndex];

    return(newTime,startTestIndex)


def isRowAllFloat(row):
    try:
        [float(x) for x in row]
        return True
    except ValueError:
        return False

def warningProcess(ADC6Vector, isLSS, newTime, startTestIndex, warningMode):

    ADC6Out = ADC6Vector.copy()
    ADC6Out[:] = 0

    if isLSS or startTestIndex == None:
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


def LSSProcessing(test, dt:float, positionVector, LSSDirection):
    parentFolder = os.path.dirname(test)
    lineFolder = os.path.dirname(parentFolder)
    zeroFile = os.path.join(lineFolder, "zero.ini")

    if not os.path.isfile(zeroFile):
        raise Exception("No zero.ini file was found.")

    with open(zeroFile, 'r') as file:
        zero = file.readline()

    zero = float(zero)
    distToLine = positionVector - zero

    Wn = 10/50

    sos = signal.butter(6, Wn, btype='low', output='sos')

    derivPosition = positionVector.diff() / dt
    derivPosition[0] = derivPosition[1] # Removes the NaN as the first element from the vector

    derivPosition = signal.sosfiltfilt(sos, derivPosition)

    return (derivPosition, distToLine)


def exportFile(testFile, table, headers:list[str]):
    with open(testFile, 'w', newline='', encoding="cp1252") as file:

        file.write(headers[0])
        file.write(headers[1])
        file.write('\t'.join(table.columns) + "\n")
        file.write(headers[2])
        table.to_csv(file, sep = "\t", index = False, header = False)
