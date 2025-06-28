from colorama import init, Fore, Style
import os

def removeCharacters(genericString: str) -> str:
    invalidCharacters = ['?', '�', '[',']', '⁻', chr(8314)]

    cleanString = genericString

    for characters in invalidCharacters:
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