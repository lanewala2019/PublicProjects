#
# Each LED is represented by a structure that describes its color and brightness#

import sys
import board
import neopixel
from time import sleep
import random
from dataclasses import dataclass
from typing import List

#
# The led matrix has MAXROW & MAXCOL, all connected in a serial fashion
# and driven by one power supply (in this case, 12VDC).
#
# A specific LED is addressed as (row*MAXCOL + col)
# and can be turned off and on by executing the appropriate function
#

MAXCOL = 50
MAXROW = 10
global pixels, cells

@dataclass
class cell:
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
	maxLED = MAXCOL * MAXROW
	pixels = neopixel.NeoPixel(board.D18, maxLED, brightness=0.5)
	pixels.fill((0,0,0))
	pixels.show()

# Light up one LED on Row X, Column Y
def setRowColumnLed(row, col, color, brightness, status):
	global pixels, cells
	led = row*MAXCOL + col
	pixels[led] = color
	cells[led].color = color
	cells[led].status = status

# Clear one LED on Row X, Column Y
def clearRowColumnLed(row, col):
	global pixels, cells
	led = row*MAXCOL + col
	pixels[led] = (0,0,0)
	cells[led].color = (0,0,0)
	cells[led].status = False

def clearAll():
	global pixels, cells
	pixels.fill((0,0,0))
	pixels.show()
	init_cells(cells, MAXROW, MAXCOL)

def init_cells(cells, maxR, maxC):
	for row in range (0, maxR):
		for col in range (0, maxC):
			idx = row*MAXCOL + col
			cells.append(cell(False,(0,0,0),0,idx))





""" MAIN """

try:
	init()

	cells  = []
	init_cells(cells, MAXROW, MAXCOL)
	#print(cells[0])
	#print(cells[0].status, cells[5].color)

	while True:
		#for row in range (0, MAXROW):
		row = 0
		for col in range (MAXCOL, -1, -1):
			#if col != 49:
			#	clearRowColumnLed(row, col+1)
			setRowColumnLed(row, col, (255,255,255), 0.5, True)
			sleep(0.05)
		#clearRowColumnLed(row, 0)
		sleep(2)
		print(cells)
except KeyboardInterrupt:
	#clearAll()
	print("Done!!!")

