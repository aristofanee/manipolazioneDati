from colorama import init, Fore, Style
from enum import Enum
import os

def removeCharacters(genericString: str, charList: list[chr]) -> str:

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
    outputString:str = []
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





    



    




