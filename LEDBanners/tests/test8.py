#
# Each LED is represented by a structure that describes its color
# and brightness#
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
#

# Pixels is how LEDs get turned on/off. Organized as 10 strands of 50
# LEDs each so as to create a matrix of 10x50.
MAXPIXELSCOL = 50
#MAXPIXELSROW = 10
MAXPIXELSROW = 10
#
# Cells is the way in which specific data is to be displayed via pixels.
# For example, "Merry Christmas" translates to 15x(8+2) pixels
# (15 letter/spaces and 8 pixels per character + 2 pixels of spacing
# between characters). So 200 cells provides for longer sets of characters
#MAXCELLSCOL = 200
MAXCELLSCOL = 50 # for testing, min number of cells
#MAXCELLSROW = 10
MAXCELLSROW = 10

global pixels, cells
global currCellsIndex, nextCellsIndex

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
			


def init():
	global pixels
	maxLED = MAXPIXELSCOL * MAXPIXELSROW
	pixels = neopixel.NeoPixel(board.D18, maxLED, brightness=0.5, auto_write=False)
	#pixels = neopixel.NeoPixel(board.D18, maxLED, brightness=0.5)
	pixels.fill((0,150,150))
	pixels.show()

# Light up one LED on Row X, Column Y
def setRowColumnLed(row, col, color, brightness, status):
	global pixels
	#led = row*MAXPIXELSCOL + col
	led = col*MAXPIXELSROW + row
	pixels[led] = color

# Clear one LED on Row X, Column Y
def clearRowColumnLed(row, col):
	global pixels
	#led = row*MAXPIXELSCOL + col
	led = col*MAXPIXELSROW + row
	pixels[led] = (0,0,0)

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
def init_cells(cells):
	start = timer()
	for col in range (0, MAXCELLSCOL):
		color = (0, col*10%255, 0)
		for row in range (0, MAXCELLSROW):
			idx = col*MAXCELLSROW + row
			cells.append(cell(False,color,0,idx))
	#print(cells)
	print("init_cells: elapsed time = ", (timer()-start))



# Populate cells matrix from "source"
def populateCells():
	start = timer()
	global cells
	# For testing purposes, populate every other element in a column
	# In real situation, data will be populated from some other source
	for col in range (0, MAXCELLSCOL-1, 5):
		for row in range (0, MAXCELLSROW):
			idx = col*MAXCELLSROW + row
			# Two ways if populating elements...
			#cells[idx].color = (0,255,0)
			#cells[idx].brightness = 0.5
			#cells[idx].idx = idx
			#cells[idx].status = True
			cells[idx] = (cell(True, (123,234,123), 0.5, idx))
	#print(cells)
	print("populateCells: elapsed time = ", (timer()-start))


#
# shift (MAXPIXELSCOL-1) columns to the left
# pixels is oriented as a contibuous strand, therefore the proper
# representation is row-oriented, ie, a full row of columns followed
# by another row of columns
#
def shiftPixelsLeft():
	global pixels

	start = timer()
	idx = 0
	for idx in range (1, MAXPIXELSCOL*MAXPIXELSROW):
		if idx%MAXPIXELSCOL == 0:
			continue
		#print("In shiftPixelsLeft: idx=",idx)
		pixels[idx-1] = pixels[idx]
	print("shiftPixelsLeft: elapsed time = ", (timer()-start))
	pixels.show()


# Always copying one column worth from current cells data and copying to the
# right-most column in pixels. 'currCellsIndex' is always the top of a 'column'
# 'cells' is organized by column not row, so adjacent cells are the rows of 
# a column.
def copyCellsToPixels(currCellsIndex):
	global pixels, cells

	start = timer()
	pixelsIndex = MAXPIXELSCOL-1 # last led of row 0
	#print("In copyCellsToPixels: currCellsIndex=",currCellsIndex," pixelsIndex=", pixelsIndex)
	for col in range (currCellsIndex, currCellsIndex+MAXCELLSROW):
		#print("In copyCellsToPixels: pixelsIndex=",pixelsIndex," col=",col)
		# We'll always be replacing contents of the right-most
		# 'column' of pixels data
		pixels[pixelsIndex] = cells[col].color
		#print("In copyCellsToPixels: pixels[",pixelsIndex,"]=",pixels[pixelsIndex]," cells[",col,"]=",cells[col])
		pixelsIndex += MAXPIXELSCOL
		#print("In copyCellsToPixels: pixelsIndex=", pixelsIndex)
		#if pixelsIndex > MAXPIXELSROW*MAXPIXELSCOL:
		#	break
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
	currCellsIndex = cellrow*MAXCELLSCOL + cellcol
	#print ("In Main: currCellsIndex=", currCellsIndex)
	while True:
		if currCellsIndex > MAXCELLSROW*MAXCELLSCOL-1:
			break
		#printRightPixels()
		shiftPixelsLeft()
		copyCellsToPixels(currCellsIndex)
		currCellsIndex += MAXCELLSROW
		#print ("In Main: after copyCellToPixels: currCellsIndex=", currCellsIndex)
		#pixels.show()
		sleep(0.1)
	clearAll()
except KeyboardInterrupt:
	clearAll()
	print("Done!!!")

