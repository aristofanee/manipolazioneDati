from colorama import init, Fore, Style
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
    

