# cycle through all 50 LEDs in reverse order; also use a function to
# select specific LED to turn on
import sys
import getopt
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

# Main entry point. Parse arg, then invoke functions to control which led
# is turned on, and then turned off
#
def main(argv):
	try:
		opts, args = getopt.getopt(argv,"hl:")
	except getopt.GetoptError:
		print ('test4.py -l <led-number>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print ('test4.py -l <led-number>')
			sys.exit()
		elif opt == '-l':
			chosenLed = int(arg)

	init()

	#sleep(2)

	row = (int)(chosenLed/MAXCOL)
	col = chosenLed % MAXCOL
	setRowColumnLed(row, col, (255,255,255), 0.5)
	sleep(1)
	clearRowColumnLed(row, col)



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



if __name__ == "__main__":
   main(sys.argv[1:])

