# cycle through all 50 LEDs n groups of 5 with random colors for each LED
# in that group
import board
import neopixel
from time import sleep
import random

maxLED = 50
pixels = neopixel.NeoPixel(board.D18, maxLED, brightness=0.5)
pixels.fill((0,0,0))
pixels.show()

# Cycle through 5 LEDs at a time
for start in range (0, 50, 5):
	end = start + 5
	for led in range (start, end):
		pixels[led] = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
	pixels.show()
	sleep(0.5)
	pixels.fill((0,0,0))
	pixels.show()
