# cycle through all 50 LEDs in reverse order; also use a function to
# select specific LED to turn on

import board
import neopixel
from time import sleep
import random

#
# The led matrix has MAXROW & MAXCOL, all connected in a serial fashion
# and driven by one power supply (in this case, 12VDC).
#
# A specific LED is addressed as (row*MAXCOL + col)
# and can be turned off and on by executing the appropriate function
#

MAXCOL = 50
MAXROW = 10
global pixels

def init():
	global pixels
	maxLED = MAXCOL * MAXROW
	pixels = neopixel.NeoPixel(board.D18, maxLED, brightness=0.5)
	pixels.fill((0,0,0))
	pixels.show()

# Light up one LED on Row X, Column Y
def setRowColumnLed(row, col, color, brightness):
	global pixels
	led = row*MAXCOL + col
	pixels[led] = color

# Clear one LED on Row X, Column Y
def clearRowColumnLed(row, col):
	global pixels
	led = row*MAXCOL + col
	pixels[led] = (0,0,0)

def clearAll():
	global pixels
	pixels.fill((0,0,0))
	pixels.show()


""" MAIN """

try:
	init()

	sleep(2)

	while True:
		#for row in range (0, MAXROW):
		row = 0
		for col in range (MAXCOL, -1, -1):
			if col != 49:
				clearRowColumnLed(row, col+1)
			setRowColumnLed(row, col, (255,255,255), 0.5)
			sleep(0.05)
		clearRowColumnLed(row, 0)
		sleep(2)
except KeyboardInterrupt:
	clearAll()

