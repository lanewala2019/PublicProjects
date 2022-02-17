#
# Program a "matrix" of individually-addressable LEDs to create a scrolling
# display of "stuff", wherein the contents scroll from right to left.
# "Displaying" means specific LEDs are turned on (e.g., a "T" is represented
# using a 5x8 "dot-matrix" character).
#
# Strands of WS2811 LEDs (50 per strand are connected serially -
# Row 0 begins at the left and ends at the right, Row 1 begins at the
# right and goes left, etc.
#
# Using the NeoPixels library, ALL the LEDs are addressed as a single array.
#
# To represent the contiguous strands as a matrix, individual 'cells' (LEDs)
# need to be addressed slightly differently - LED[0] at the left-most end
# (i.e., 'column' 0 of the 'matrix') of 'Row' 0, LED[50] at the right-most end
# (i.e., column 49 of the matrix) of Row 1, LED[100] at the left-most end
# of 'Row' 2 etc.
#
# The piece of text is provided by a command-line argument. A lookup in a table
# gives us the led pattern that needs to be lit up to render the piece of text.
#

import os
import sys
import logging
import logging.handlers
import glob
import argparse
import board
import neopixel
from time import sleep
import random
from dataclasses import dataclass
from typing import List
from timeit import default_timer as timer
from fonts8x8 import font8x8 as f # local file
import RPi.GPIO as GPIO

#
# The led matrix has MAXROW & MAXCOL, all connected in a serial fashion
# and driven by one power supply (in this case, 12VDC).
#
# A specific LED is addressed as (row*MAXCOL + col)
# and can be turned off and on by executing the appropriate function
# with the special proviso that columns in even rows are counted left
# to right, and columns in odd rows are counted right to left. This is
# because multiple strands are connected serially, and the physical
# structure causes the strands to be snaked right-to-left, then left-to-right,
# then right-to-left, etc.
#


# Pixels is how LEDs get turned on/off. Organized as 10 strands of 50
# LEDs each so as to create a matrix of 10x50.
#
global MAXPIXELSCOL
global MAXPIXELSROW
#
# Cells is the way in which specific data is to be displayed via pixels.
# For example, "Merry Christmas" translates to 15x(8+2) pixels
# (15 letter/spaces and 8 pixels per character + 2 pixels of spacing
# between characters). So 200 cells provides for longer sets of characters
#
global MAXCELLSCOL
global MAXCELLSROW

global NUMCHARROW
global NUMCHARCOL

global pixels, cells
global currCellsIndex, nextCellsIndex, cellsUsed
global text, file, blink

global logger

global DEBUG_LEVEL

#
# class "cell" contains the status of each LED. Data in "cells" is populated
# from some source (e.g., file). "cells" data is copied into the appropriate
# "pixels" so that "pixels" contains the current state of each LED
#
@dataclass
class cell:
	status: int
	color: (int, int, int)
	brightness: float
	idx: int

	def __init__(self, status, color, brightness, idx):
		self.status = status
		self.color = color
		self.brightness = brightness
		self.idx = idx

	def __repr__(self):
		return("cell (status={}, color={}, brightness={}, idx={})" .format(self.status, self.color, self.brightness, self.idx))

	def __eq__(self, check):
		return((self.status, self.color, self.brightness, self.idx) == ((check.status, check.color, check.brightness, check.idx)))




# 'init()' sets up the neopixels portion. THis results in a one-dimensional
# array of LEDs. "pixels.fill()" allows all the LEDs to be initialized to a
# specific state (the color (0,150,150) was chosen randomly...)
#
# "board.D18" indicates that board pin 18 on a Raspberry Pi is being used to
# send the appropriate data signal to the strand(s).
#
def init():
	global pixels
	global MAXPIXELSROW, MAXPIXELSCOL

	maxLED = MAXPIXELSCOL * MAXPIXELSROW
	pixels = neopixel.NeoPixel(board.D18, maxLED, brightness=0.5, auto_write=False)
	for led in range (0, MAXPIXELSROW*MAXPIXELSCOL-1):
		pixels[led] = (0, 0, 0)
	pixels.show()

#
# A simple utility function to reset all LEDs to off.
#
def clearAll():
	global pixels, cells
	pixels.fill((0,0,0))
	pixels.show()
	init_cells(cells)


# initialize cells matrix (this will hold the state of each LED in the matrix &
# corresponds to the each LED addressed/controlled through pixels library. Each
# cell (LED) in the matrix maintains the color/brightness/status of a particular
# LED. There's not really a matrix as the LEDs are continued in one contigous
# strand, but easier to visualize if thinking in terms of a grid.
#
def init_cells(cells):
	global MAXCELLSROW, MAXCELLSCOL
	global logger

	#print("init_cells(): logger=", logger)

	start = timer()
	color = (0, 0, 0)
	for col in range (0, MAXCELLSCOL):
		for row in range (0, MAXCELLSROW):
			idx = col*MAXCELLSROW + row
			cells.append(cell(0,color,0,idx))
	logger.log(logging.DEBUG, "In init_cells() cells=[{}]".format(cells))
	logger.log(logging.DEBUG, "init_cells(): elapsed time=[{}]".format(timer()-start))



# Populate cells matrix from "source". "source" is anything that contains
# the representation of the text or object to be scrolled using neopixels.
#
# A source consists of two parts:
# 1. A matrix that describes the dot-matrix "structure" of specific
#    alphanumerics in a 10x10 matrix, with 5 columns x 8 rows used to
#    describe a specific character
# 2. A description of the text to be scrolled, e.g., "Merry Christmas".
#    In turn, the text consists of three parts - text, text color & background
#	 color (delimited by "|")
#
# The "cells" matrix then stores the dot-matrix representation of the text
# by using the individual representations. The use of this indirection makes
# it simple to "replay" content from "cells" into "pixels", and thus keep
# repeating the text, with a "new character" entering the display from the
# right.
#
def populateCells(banner):
	start = timer()
	global cells
	global cellsUsed
	global MAXCELLSROW, MAXCELLSCOL
	global blink
	global logger

	cellsCol = 0 # index into the 'cells' array

	#
	# Use text that is to be displayed to determine which columns/rows
	# in 'cells' need to be marked as LEDs to turn on or not.
	#
	# "text" is a list with either one entry (cmdline used to set text)
	# or contents of a file
	#
	for rec in banner:
		text = rec.split("|")[0]
		textColor = rec.split("|")[1]
		textBrightness = rec.split("|")[2]
		bkgrndColor = rec.split("|")[3]
		bkgrndBrightness = rec.split("|")[4]

		logger.log(logging.DEBUG, "In populateCells: processing text=[{}] with tcolor=[{}] & bcolor=[{}] ,cellsCol=[{}]".format(text,textColor,bkgrndColor,cellsCol))

		splitText = list(text)
		logger.log(logging.DEBUG, "populateCells: splitText={}".format(splitText))

		#
		# Before first character in banner, configure two columns of "background";
		# makes things look a bit better
		cellsRow = 0
		for rows in range (0, MAXCELLSROW,1):
			for extraCols in range (cellsCol, cellsCol+2, 1):
				idx = extraCols*MAXCELLSROW + rows
				cells[idx] = (cell(1, colorStrToInt(bkgrndColor), bkgrndBrightness, idx))
				logger.log(logging.DEBUG, " before char, extra background cell, cell={}".format(cells[idx])) 
		cellsCol += 2
		logger.log(logging.DEBUG, "beginning of first banner char, spacers added; cellsCol={}".format(cellsCol))

		# Process each character in the banner text
		for i in splitText:
			logger.log(logging.DEBUG, "In populateCells: processing ch=[{}]".format(i))

			charFont = lookupFont(i)
			#
			# Each 'charFont' represents the set of LEDs that must be lit
			# to 'show' a particular character. Thus, 'charFont' is a 8x8
			# matrix that must be used to set the proper LEDs to a particular
			# color in the 'cells' matrix
			#
			for d in charFont:
				# Each character starts at row zero
				cellsRow = 0
				for bit in range (NUMCHARCOL, 0, -1):
					idx = cellsCol*MAXCELLSROW + cellsRow
					if isBitSet(d, bit):
						# mark cell as on
						cells[idx] = (cell(1, colorStrToInt(textColor), textBrightness, idx))
						logger.log(logging.DEBUG, " bit ON, cell={}".format(cells[idx])) 
					elif blink == 'on':
						# mark which LEDs should flicker
						cells[idx] = (cell(2, getRandomColor(0,10,0,10,0,10), 0, idx))
						logger.log(logging.DEBUG, " blink ON, cell={}".format(cells[idx])) 
					else:
						# any other LED is a "background" LED
						cells[idx] = (cell(1, colorStrToInt(bkgrndColor), bkgrndBrightness, idx))
						logger.log(logging.DEBUG, " background cell, blink OFF, no text, cell={}".format(cells[idx])) 
					# move down the column to the next row
					cellsRow += 1
					logger.log(logging.DEBUG, " ")
				logger.log(logging.DEBUG, " ")
				# Done with column, proceed to the next column
				cellsCol += 1
			logger.log(logging.DEBUG, "end of char: {}, cellsCol={}".format(i, cellsCol))
			#
			# End of character. Provide "sopacing" before next character:
			# Skip 2 columns in 'cells' to provide spacing between characters, but set the
			# "background" color of the cells for these columns
			cellsRow = 0
			for rows in range (0, MAXCELLSROW,1):
				for extraCols in range (cellsCol, cellsCol+2, 1):
					idx = extraCols*MAXCELLSROW + rows
					cells[idx] = (cell(1, colorStrToInt(bkgrndColor), bkgrndBrightness, idx))
					logger.log(logging.DEBUG, " extra background cell, cell={}".format(cells[idx])) 
			cellsCol += 2
			logger.log(logging.DEBUG, "end of char:{} and spacer added; cellsCol={}".format(i,cellsCol))
		#
		# end of current line of text; if more lines, add more empty cells
		#
		# TODO: next 16 columns must be either off or random on
		cellsCol += 16
		debugStr = "end of line: and spacer added; cellsCol=", cellsCol
		logger.log(logging.DEBUG, "end of line: and spacer added; cellsCol={}".format(cellsCol))
			

	# number of 'cells" used
	cellsUsed = cellsCol*MAXCELLSROW
	logger.log(logging.DEBUG, "In populateCells: cellsUsed={}".format(cellsUsed))

	logger.log(logging.DEBUG, "populateCells: elapsed time = {}".format((timer()-start)))


#
# shift (MAXPIXELSCOL-1) columns to the left.
#
# 'pixels' is oriented as a contibuous strand, therefore the proper
# representation is row-oriented, ie, a full row of columns followed
# by another row of columns. Each row's addressable LEDs are actually
# reversed in direction from the previous row.
#
def shiftPixelsLeft():
	global pixels
	global MAXPIXELSROW, MAXPIXELSCOL
	global logger

	start = timer()
	for row in range (0, MAXPIXELSROW):
		for col in range (0, MAXPIXELSCOL):
			idx = row*MAXPIXELSCOL + col
			if idx == 0:
				continue
			if ((int)(idx/MAXPIXELSCOL)%2 == 0):
				logger.log(logging.DEBUG, "in shiftPixelsLeft: even: shift from {} to {}".format(idx, idx-1))
				pixels[idx-1] = pixels[idx]
			else:
				idx = (row+1)*MAXPIXELSCOL-(col+1)
				logger.log(logging.DEBUG, "in shiftPixelsLeft: odd: shift from {} to {}".format(idx-1, idx))
				pixels[idx] = pixels[idx-1]
			
	pixels.show()
	logger.log(logging.DEBUG, "shiftPixelsLeft: elapsed time = {}".format((timer()-start)))


# Always copying one column worth from current cells data and copying to the
# right-most column in pixels. 'currCellsIndex' is always the top of a 'column'
# 'cells' is organized by column not row, so adjacent cells are the rows of 
# a column.
def copyCellsToPixels(currCellsIndex):
	global pixels, cells
	global MAXPIXELSROW, MAXPIXELSCOL
	global MAXCELLSROW, MAXCELLSCOL
	global logger

	start = timer()
	pixelsIndex = MAXPIXELSCOL-1 # last led of row 0

	logger.log(logging.DEBUG, "In copyCellsToPixels: currCellsIndex={}, pixelsIndex={}".format(currCellsIndex, pixelsIndex))

	pixelsRow = (int)(pixelsIndex/MAXPIXELSCOL)
	for cellIdx in range (currCellsIndex, currCellsIndex+MAXCELLSROW):
		if pixelsRow%2 == 0:
			# Even row
			idx = (pixelsRow+1)*MAXPIXELSCOL-1
			logger.log(logging.DEBUG, "copyCellsToPixels: even: idx={} cellIdx={} color={}".format(idx, cellIdx, cells[cellIdx].color))
			pixels[idx] = cells[cellIdx].color
		else:
			# Odd row
			idx = pixelsRow*MAXPIXELSCOL
			logger.log(logging.DEBUG, "copyCellsToPixels: odd: idx={} cellIdx={} color={}".format(idx, cellIdx, cells[cellIdx].color))
			pixels[idx] = cells[cellIdx].color
		pixelsRow += 1
		
	pixels.show()
	logger.log(logging.DEBUG, "copyCellsToPixels: elapsed time = {}".format((timer()-start)))


#
# convert str "(xx, yy, zz)" to (xx, yy, zz), i.e., remove leading/traialing
# '('/')' and convert string numbers to int
def colorStrToInt(tColor):
	global logger

	substr = tColor[1:-1]
	rgblist = list(map(int,substr.split(",")))
	colorInt = (rgblist[0], rgblist[1], rgblist[2])
	logger.log(logging.DEBUG, " colorStrToInt: color=[{}]".format(colorInt))
	return colorInt


# Retrieve font defition for a provided character
def lookupFont(ch):
	global logger

	intCh = ord(ch)
	idx = intCh-f.baseOffset
	logger.log(logging.DEBUG, "intCh={},  idx={}, baseOffset={}".format(intCh,idx,f.baseOffset))
	return (f.fonts8x8[idx])


# Extract bits from a hex value. Returns True if bit is set, False otherwise
def isBitSet(num, bit):
	return (bool(num & 1 << bit - 1))


# helper function to return a random color based on lo/hi R/G/B ranges
def getRandomColor(lR, hR, lG, hG, lB, hB):
	r = random.random()
	if (int(r*10))%2 == 1:
		R = random.randint(lR, hR)
		G = random.randint(lG, hG)
		B = random.randint(lB, hB)
	else:
		R = G = B = 0
	color = (R, G, B)
	return (color)

#
# Check filesystem to see if any file with the extension '.bannertext' has been
# created/modified.
def chkModifiedBannerFile(pattern):
	files = glob.glob(pattern)
	lastfile = max(files, key=os.path.getmtime)
	return lastfile

#
# Read banner text file into a list
# text file contains strings of the form : color|text
def readBannerTextFile(file):
	global logger

	start = timer()
	with open(file) as f:
		linesList= f.read().splitlines()
	if linesList!= None:
		fileRead = file
		logger.log(logging.DEBUG, "readBannerText: linesList=[{}]".format(linesList))
		if logger.level == logging.DEBUG:
			for line in linesList:
				logger.log(logging.DEBUG, "readBannerText: line=[{}]".format(line))
			logger.log(logging.DEBUG, "readBannerTextFile: elapsed time = {}".format((timer()-start)))
		return (linesList)
	else:
		return None


# for debugging purposes
def printRightPixels():
	global logger

	for idx in range(MAXPIXELSROW*MAXPIXELSCOL-1, MAXPIXELSCOL-MAXPIXELSROW-1, -MAXPIXELSCOL):
		logger.log(logging.DEBUG, "pixels[{}]={}".format(idx, pixels[idx]))


""" MAIN """
def main(argv):
	global cells, currCellsIndex, cellsUsed
	global MAXPIXELSROW, MAXPIXELSCOL
	global MAXCELLSROW, MAXCELLSCOL
	global NUMCHARROW, NUMCHARCOL
	global blink
	global logger


	MAXPIXELSROW = 8
	MAXPIXELSCOL = 50
	MAXCELLSROW = MAXPIXELSROW
	MAXCELLSCOL = 0 # just a placeholder (will be calculated)
	NUMCHARROW = 8
	NUMCHARCOL = 8

	#
	# initialize logger
	LOG_FILENAME = './logs/log.out'
	logger = logging.getLogger('Logger')

	banner = []

	dirToChk = "." # current directory will be root for file change checks


	# process command-line args
	# One of two args are possible (if both are given, we'll use one
	# The args are either a piece of text, or a file containing the text
	#
	# Initialize parser
	parser = argparse.ArgumentParser()

	# Adding optional argument
	parser.add_argument("-f", "--File")
	parser.add_argument("-t", "--Text")
	parser.add_argument("-b", "--Blink")
	parser.add_argument("-l", "--Log")

	# Read arguments from command line
	args = parser.parse_args()
	file = args.File
	text = args.Text
	blink = args.Blink
	logStr = args.Log
	
	if logStr == 'DEBUG':
		log = logging.DEBUG
	elif logStr == 'WARNING':
		log = logging.WARNING
	elif logStr == 'INFO':
		log = logging.INFO
	elif logStr == 'CRITICAL':
		log = logging.CRITICAL
	elif logStr == 'FATAL':
		log = logging.FATAL
	else:
		log = logging.FATAL

	logger.setLevel(log)
	logHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=(1024*1024*2), backupCount=7)
	logger.addHandler(logHandler)
	formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
	logHandler.setFormatter(formatter)

	# If using file, program will render contents of each line
	# from the file with a brief delay between lines; then repeat
	# from the beginning
	#
	# If using text, program will repeat the text after a brief
	# delay.
	#
	# If both args are given, "file" will be given preference
	#
	# The -b option tells us whether to cause random blinking
	# patterns to go below the scrolling text



	# See if this helps using same GPIO pin between two scripts
	#GPIO.setwarnings(False)

	init()


	#
	# text to scroll can be provided either on cmdline or in a file
	# (obviously the cmdline must provide the name of a file.  File
	# naming conventions - file MUST have ".bannertext" extension.
	#
	if text != None:
		if len(text) > 0:
			banner.append(text)
	if file != None:
		if  len(file) > 0:
			# read file into bannerText list
			banner = readBannerTextFile(file)
			if banner == None:
				print("Uh Oh! Could not read file:["+file+"]")
				exit()

	if file == None and text == None:
		print("One of '-t' or '-f' option is required.")
		print("Usage: sudo python3 <prog> {-t '(r,g,b)|text' | -f xxx.bannertext} [-b {on|off}] [-l {DEBUG|INFO|FATAL|CRITICAL|WARNING}]")
		exit()
	if blink != None:
		if blink != 'on' and blink != 'off':
			print("Permitted values for -b option are 'on' or 'off'")
			print("Usage: sudo python3 <prog> {-t '(r,g,b)|text' | -f xxx.bannertext} [-b {on|off}] [-l {DEBUG|INFO|FATAL|CRITICAL|WARNING}]")
			exit()

	
	logger.log(logging.INFO, "Cmdline args: text=[{}], file=[{}] blink=[{}], log=[{}]".format(text, file, blink, log))

	logger.log(logging.DEBUG, "banner={}".format(banner))

	# There are two parts in banner: a color and a text separated by '|'
	# Count total number of characters in banner; use that
	# to set MAXCELLSCOL before init_cells() is invoked
	# Each line of text has characters that each take up NUMCHARCOL columns
	cnt = 0

	for b in banner:
		bc = b.split("|")
		bcBC = bc[3] #background color
		bcTC = bc[1] #text color
		bcT = bc[0] #text
		cnt += len(bcT)*(NUMCHARCOL+2) # extra for 'spacing' after each "char" in bannertext
		logger.log(logging.DEBUG, "main:[{}], len(bcT)=[{}], cnt=[{}]".format(bcT, len(bcT), cnt))
		logger.log(logging.DEBUG, "main: bcTC=[{}], gcBC=[{}], bcT=[{}]".format(bcTC, bcBC, bcT))


	cnt = cnt + 16 # extra 'spacing' after each line of text
	logger.log(logging.DEBUG, "main: calculated cells count=[{}]".format(cnt))

	MAXCELLSCOL = cnt
	cells  = []
	init_cells(cells) #initialize the cells array - basically to zeroes...

	populateCells(banner) #inituialize info from banner(s) collected from cmdline or from file


	cellrow = 0
	cellcol = 0

	currCellsIndex = 0
	logger.log(logging.DEBUG, "In main: currCellsIndex=[{}]".format(currCellsIndex))


	# Main section: Basic process is to read the banner info each cycle (only applies when a file is used) in case 
	# the file contents were changed in between interations. Then shift pixels left one "col", and populate the right-most
	# "col"s with elements from the "cells" array. Repeat. On each iteration, some checks to see if we've reached the
	# end of the cells array or if we've reached the edge of the LED matrix.
	try:
		while True:
			# Have we processed everything in cells?
			if currCellsIndex > cellsUsed:
				logger.log(logging.DEBUG, "In Main: currCellsIndex={} cellsUsed={} - resetting currCellsIndex to 0".format(currCellsIndex, cellsUsed))
				currCellsIndex = 0

				# entire cotents of 'cells' has been processed
				# Re-read any file containing text in case
				# it may have changed...
				# & repopulate the 'cells' matrix
				if file != None:
					banner = readBannerTextFile(file)
					if banner == None:
						print("Uh Oh! Could not read file:["+file+"]")
						exit()
					logger.log(logging.DEBUG, "banner text file contents:[{}]".format(banner))
					populateCells(banner)
			printRightPixels()

			# Basic loop is:
			#  shift pixels left one 'column'
			#  insert 'new' 'column' at right-most point
			#  show pixels
			shiftPixelsLeft()
			copyCellsToPixels(currCellsIndex)
			pixels.show()

			# where in cells matrix are we? i.e., column
			# of data has been copied from cells to pixels,
			# so we can shift the index into 'cells' to get
			# ready for the next column to be handled
			currCellsIndex += MAXCELLSROW
			logger.log(logging.DEBUG, "In Main: after copyCellToPixels: currCellsIndex=[{}]".format(currCellsIndex))
			#sleep(0.03)

		clearAll() # at end of one cycle, turn off all LEDs so we can repeat everything from a clean slate
	except KeyboardInterrupt:
		clearAll() # at end (received a terminate signal) reset all LEDs to a known (off) state
		print("Done Scrolling LEDs using file: ", file, " !!!")





if __name__ == "__main__":
	main(sys.argv[1:])

