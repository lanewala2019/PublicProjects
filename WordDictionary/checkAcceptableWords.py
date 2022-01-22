#
# In order to constrain people from using acceptable words when constructing a "banner",
# only an acceptable list of words is permitted.
#
# This script examines each word provided and checks to see if it is one of those in the
# acceptable list.
#
# The list of words is managed via a sorted list.
#

import acceptableWordsList

def checkAcceptableWords(bannerTextList):
    acceptable = acceptableWordsList.wordList
    unacceptable = ""
    #print("checkAcceptableWords: ", bannerTextList)
    #print("wordList=", acceptable)
    for el in bannerTextList:
        # capitalize the word before checking (acceptable has all words capitalized)
        if el.title() not in acceptable:
            unacceptable = unacceptable + " " + el
    #print ("unacceptable=", unacceptable)
    return unacceptable

