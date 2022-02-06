import sys
import subprocess
import signal
import os
import time
from common import * # template names, path variables etc.


# create (R,G,B) tuple given a hex color string
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv //3], 16) for i in range(0, lv, lv // 3))



# given a string delimted by "|", split into groups of five segments, with
# the second and fourth segments to be enclosed in "()" - they represent color
#
# The reason this needs to be created this way is that the program that renders
# this in a LED matrix expects a file with a specific syntax
def generateLinesFromText(txt):
    l1 = txt.split('|') # inital split on '|'
    #print("generateLinesFromText (a): l1=", l1)

    # fix up the color components
    # convert hex representation to comma-separated integer enclosed in parentheses
    for idx in range (0, len(l1), 5):
        l1[idx+1] = str(hex_to_rgb(l1[idx+1]))
        l1[idx+3] = str(hex_to_rgb(l1[idx+3]))
#        l1[idx+1] = "("+l1[idx+1]+")"
#        l1[idx+3] = "("+l1[idx+3]+")"
    #print("generateLinesFromText (b): l1=", l1)

    # next the groups of five represent one line in a file, so make a "|" separated string for each grp of five
    n = 5
    grps = []
    while len(l1):
	    grps.append('|'.join(l1[:n]))
	    l1 = l1[n:]
    #print("generateLinesFromText: grps=[",grps,"]")
    return grps
	

# main entry point into the functions in this module. Purpose is to write "dtext"
# to a file "fn". "dtext" must be split into multiple lines to be written to the file.
def createBannerFile(fn, dtext):
    #print("createBannerFile: dtext=",dtext)
    lines = generateLinesFromText(dtext)
	
    # Each 'line' consists of three strings separated by '|'. Before writing to file,
    # several conversions have to take place:
    # a. the 2nd and 3rd strings have to be modified to enclose in parenthese
    # b. the string to be written to the file is : text|fcolor|bcolor, where fcolor and bcolor
    # are of the form "(g,r,b)"
    #
    f = open(fn, "w+")

    # The structure of the .bannertext file is:
   	#	text|fcolor|bcolor
    #	text|fcolor|bcolor
    #	.
    #	.
    # with color in parentheses like "(r,g,b)"
    #
    # 'dtext' contains a string of the form:
    # 	text|fcolor|bcolor|text|fcolor|bcolor....
    # organized as:
    #	text|nn,nn,nn|nn,nn,nn
    #
    # So dtext needs to split up appropriately, and the color component modified
    # before file is written to
    #
    for l in lines:
    	f.write(l+"\n")
    f.close()
    return


# This function will use subprocess to kick off a child process 
def startSubProcess(bannerFile, process):
    #print ('Start subrocess: bannerFile=[',bannerFile,"]")
    pathname = LEDLIGHT_PATH+SCROLLINGLED_PROGRAM+' -f '+ BANNER_PATH+bannerFile
    cmd = 'sudo python '+pathname
    process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
    return process       


# issue a interrupt to the child to terminate it
def stopSubProcess(pid):
    #print ('Stop subrocess: pid=',pid)

    if check_pid(pid) == True:
        os.killpg(os.getpgid(pid), signal.SIGINT)
    return

# Check if a pid exists
def check_pid(pid):        
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True



# Search through aggregateFileContent list for fileName and set its pid to passed-in one
def updateBannerPidInfo(fn, procPid, aggrContent):
    for content in aggrContent:
        if content[2] == fn:
            #print("updateBannerPidInfo: found match on ", fn," - at content=",content)
            content[1] = procPid

            # this is a match for the banner to be run; set its video content to be visible
            content[0] = 'style=visibility:visible'
    #print("updateBannerPidInfo: aggrContent=$%$% ", aggrContent, "$%$%")
    return (aggrContent)



# Search through aggregateFileContent list for pid and reset that element to ''
def resetBannerPidInfo(procPid, aggrContent):
    for content in aggrContent:
        if content[1] == procPid:
            #print("resetBannerPidInfo: found match on ", procPid," - at content=",content)
            content[1] = '' # reset pid

            # banner stopped; set its video visibility to hidden
            content[0] = 'style=visibility:hidden'
    #print("resetBannerPidInfo: aggrContent=$%$% ", aggrContent, "$%$%")
    return (aggrContent)


# check in the aggrContent to see if there is a pid asspciated with this fileName. Return True if there is.
def doesPidExist(fileName, aggrContent):
    for content in aggrContent:
        if content[2] == fileName:
            if len(content[1]) > 0:
                return (True)
    return (False)


# Only one banner can be run at any time, because of limitations of the WS2811 LED strands.
# Check to ensure that there is no other entry with a pid in it (that means a banner is
# already running).
def anyOtherPidsExist(aggrContent):
    for content in aggrContent:
        if len(content[1]) > 0:
            return (True)
    return (False)


#
# get files in the banners directory and build the aggregate files content list
#
def makeAggregateFilesContent():
    global aggregateFilesContent

    files = os.listdir(BANNER_PATH)
    #print("banner: files=", files)
    aggregateFilesContent = []

    while files:
        # Each "row" in the contents array represents a table row rendered in HTML.
        # To maintain proepr state, certain bits must be preserved across the page rendering.
        # In order to know what banner is running, its pid must be captured (note the banner
        # process is a separate sub-process so we need to know ots pid)
        # Further, rather than clutter up the web page, only the currently-running banner
        # will have its video element displayed, & so we must capture that cell's visibility state
        #
        # After initialization, this array is passed back and forth between the HTML template and
        # the python scripts.
        #
        # When a banner is "run"/"stopped", a couple of functions in webAppUtils.py are used
        # to set/unset visibility of the video cell (via the contents[] array)
        content = [] # the content of a specific file in a list
        content.append("style=visibility:hidden") #initialize video cell visibility
        content.append("") #placeholder for process pid (when running as a sub-process)
        file = files.pop()
        with open(BANNER_PATH+file, "r") as f:
            txt = f.read()
        txt = txt.replace('\n', '<br>')
        # add filename to the list to render (without the .bannertext extension)
        file1 = file
        fileStr = file1[:file1.index(".bannertext")]
        content.append(fileStr) # 3rd element in a list is the filename without the extension
        # now append the file contents
        content.append(txt) # gather content of a specific file
        # finally, append this whole thing as a "row" to be rendered
        aggregateFilesContent.append(content) # gather content of all files
    #print("banner(): aggregateFilesContent=***",aggregateFilesContent,"***")
    return (aggregateFilesContent)
