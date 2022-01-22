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

import sys
import board
import neopixel
from time import sleep
import random
from dataclasses import dataclass
from typing import List
from timeit import default_timer as timer

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
MAXPIXELSCOL = 50
MAXPIXELSROW = 3
#
# Cells is the way in which specific data is to be displayed via pixels.
# For example, "Merry Christmas" translates to 15x(8+2) pixels
# (15 letter/spaces and 8 pixels per character + 2 pixels of spacing
# between characters). So 200 cells provides for longer sets of characters
#
MAXCELLSCOL = 200
MAXCELLSROW = MAXPIXELSROW

global pixels, cells
global currCellsIndex, nextCellsIndex, cellsUsed

#
# class "cell" contains the status of each LED. Data in "cells" is populated
# from some source (e.g., file). "cells" data is copied into the appropriate
# "pixels" so that "pixels" contains the current state of each LED
#
@dataclass
class cell:
	status: bool
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
	maxLED = MAXPIXELSCOL * MAXPIXELSROW
	pixels = neopixel.NeoPixel(board.D18, maxLED, brightness=0.5, auto_write=False)
	for led in range (0, MAXPIXELSROW*MAXPIXELSCOL-1):
		#pixels[led] = (random.randint(50,255),random.randint(50,255),random.randint(50,255))
		pixels[led] = (10, 10, 10)
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
	start = timer()
	for col in range (0, MAXCELLSCOL):
		color = (0, 0, 0)
		for row in range (0, MAXCELLSROW):
			idx = col*MAXCELLSROW + row
			cells.append(cell(False,color,0,idx))
	#print(cells)
	print("init_cells: elapsed time = ", (timer()-start))



# Populate cells matrix from "source". "source" is anything that contains
# the representation of the text or object to be scrolled using neopixels.
#
# A source consists of two parts:
# 1. A matrix that describes the dot-matrix "structure" of specific
#    alphanumerics in a 10x10 matrix, with 5 columns x 8 rows used to
#    describe a specific character
# 2. A description of the text to be scrolled, e.g., "Merry Christmas".
#
# The "cells" matrix then stores the dot-matrix representation of the text
# by using the individual representations. The use of this indirection makes
# it simple to "replay" content from "cells" into "pixels", and thus keep
# repeating the text, with a "new character" entering the display from the
# right.
#
def populateCells():
	start = timer()
	global cells
	global cellsUsed
	# For testing purposes, populate the half the MAXPIXELSCOL elements
	# into cells structure.
	# In real situation, data will be populated from some other source
	for col in range (0, (int)(MAXPIXELSCOL/2)):
		for row in range (0, MAXCELLSROW):
			idx = col*MAXCELLSROW + row
			# Two ways if populating elements...
			#cells[idx].color = (0,255,0)
			#cells[idx].brightness = 0.5
			#cells[idx].idx = idx
			#cells[idx].status = True
			cells[idx] = (cell(True, (123,234,123), 0.5, idx))
	# calculate maxpixels in the cells matrix that have been used
	# for test purposes, we had used just MAXPIXELSCOL, i.e., 50
	# 15 'spacer' cells added to avoid run-ons on repeat
	cellsUsed = (int)(MAXPIXELSCOL/2)*MAXCELLSROW+15
	print("In populateCells: cellsUsed=",cellsUsed)
	#print(cells)
	print("populateCells: elapsed time = ", (timer()-start))


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

	start = timer()
	for row in range (0, MAXPIXELSROW):
		for col in range (0, MAXPIXELSCOL):
			idx = row*MAXPIXELSCOL + col
			if idx == 0:
				continue
			if ((int)(idx/MAXPIXELSCOL)%2 == 0):
				#print("in shiftPixelsLeft: even: shift from ", idx, " to ", idx-1)
				pixels[idx-1] = pixels[idx]
			else:
				idx = (row+1)*MAXPIXELSCOL-(col+1)
				#print("in shiftPixelsLeft: odd: shift from ", idx-1, " to ", idx)
				pixels[idx] = pixels[idx-1]
			
	pixels.show()
	print("shiftPixelsLeft: elapsed time = ", (timer()-start))


# Always copying one column worth from current cells data and copying to the
# right-most column in pixels. 'currCellsIndex' is always the top of a 'column'
# 'cells' is organized by column not row, so adjacent cells are the rows of 
# a column.
def copyCellsToPixels(currCellsIndex):
	global pixels, cells

	start = timer()
	pixelsIndex = MAXPIXELSCOL-1 # last led of row 0
	#print("In copyCellsToPixels: currCellsIndex=",currCellsIndex," pixelsIndex=", pixelsIndex)

	pixelsRow = (int)(pixelsIndex/MAXPIXELSCOL)
	for cellIdx in range (currCellsIndex, currCellsIndex+MAXCELLSROW):
		if pixelsRow%2 == 0:
			# Even row
			idx = (pixelsRow+1)*MAXPIXELSCOL-1
			#print("copyCellsToPixels: even: idx = ", idx, " cellIdx=", cellIdx)
			pixels[idx] = cells[cellIdx].color
		else:
			# Odd row
			idx = pixelsRow*MAXPIXELSCOL
			#print("copyCellsToPixels: odd: idx = ", idx, " cellIdx=", cellIdx)
			pixels[idx] = cells[cellIdx].color
		pixelsRow += 1
		
	pixels.show()
	print("copyCellsToPixels: elapsed time = ", (timer()-start))


# for debugging purposes
def printRightPixels():
	for idx in range(MAXPIXELSROW*MAXPIXELSCOL-1, MAXPIXELSCOL-MAXPIXELSROW-1, -MAXPIXELSCOL):
		print("pixels[",idx,"]=",pixels[idx])


""" MAIN """

try:
	init()

	cells  = []
	init_cells(cells)
	#print(cells[0])
	#print(cells[0].status, cells[5].color)

	populateCells()

	cellrow = 0
	cellcol = 0
	#currCellsIndex = cellrow*MAXCELLSCOL + cellcol
	currCellsIndex = 0
	#print ("In Main: currCellsIndex=", currCellsIndex)
	while True:
		if currCellsIndex > cellsUsed:
			print("In Main: currCellsIndex=", currCellsIndex, " cellsUsed=", cellsUsed," - resetting currCellsIndex to 0")
			currCellsIndex = 0
		#printRightPixels()
		shiftPixelsLeft()
		copyCellsToPixels(currCellsIndex)
		currCellsIndex += MAXCELLSROW
		#print ("In Main: after copyCellToPixels: currCellsIndex=", currCellsIndex)
		pixels.show()
		sleep(0.05)
	clearAll()
except KeyboardInterrupt:
	clearAll()
	print("Done!!!")

