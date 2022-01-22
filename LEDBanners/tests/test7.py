
import sys
from dataclasses import dataclass
from typing import List

#

MAXCOL = 5
MAXROW = 5
global cells

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
			

# initialize cells matrix (this will hold the state of each LED in the matrix &
# corresponds to the each LED addressed/controlled through pixels library. Each
# cell (LED) in the matrix maintains the color/brightness/status of a particular
# LED. There's not really a matrix as the LEDs are continued in one contigous
# strand, but easier to visualize if thinking in terms of a grid.
def init_cells(cells, maxR, maxC):
	for row in range (0, maxR):
		for col in range (0, maxC):
			idx = row*MAXCOL + col
			cells.append(cell(False,(0,0,0),0,idx))

# Populate cells matrix from "source"
def populateCells():
	global cells
	print("MAXROW = ",MAXROW," MAXCOL=", MAXCOL)
	#for row in range (0, MAXROW-1):
	row = 0
	for col in range (0, MAXCOL-1):
		idx = row*MAXCOL + col
		print("idx=",idx)
		#cells[idx].color = (0,255,0)
		#cells[idx].brightness = 0.5
		#cells[idx].idx = idx
		#cells[idx].status = True
		cells[idx] = (cell(True, (0,255,0), 0.5, idx))


""" MAIN """

cells  = []
init_cells(cells, MAXROW, MAXCOL)
#
# individual elements of the cells matrix can be addressed
# as indicated in the commented-out print statements below
#print(cells[0])
#print(cells[0].status, cells[5].color)

populateCells()
print(cells)
cells[0] = (cell(True, (0,255,0), 0.5, 0))
print(cells[0])

