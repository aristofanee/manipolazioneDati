def removeCharacters(genericString):
    invalidCharacters = ['?', '�', '[',']', '⁻', chr(8314)]

    cleanString = genericString

    for characters in invalidCharacters:
        cleanString = cleanString.replace(characters, '')

    return cleanString