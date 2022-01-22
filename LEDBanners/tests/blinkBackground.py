# 
# Create a blinking "background" for the WS2811 strips`
#
import board
import neopixel
from time import sleep
from timeit import default_timer as timer
import random
import RPi.GPIO as GPIO


#GPIO.setwarnings(False)

MAXPIXELSROW = 8
MAXPIXELSCOL = 50

pixels = neopixel.NeoPixel(board.D12, MAXPIXELSROW*MAXPIXELSCOL, brightness=0.5, auto_write=False)


max = MAXPIXELSROW*MAXPIXELSCOL
try:
	while True:
		start = timer()
		color = (random.randint(32,127),random.randint(10,64),random.randint(10,32))
		idx = random.randint(0, max-1)
		pixels[idx] = color
		pixels.show()
		pixels[idx] = (0,0,0)
		pixels.show()
		print("elapsed time = ", (timer()-start))
except KeyboardInterrupt:
	pixels.fill((0,0,0))
	pixels.show()
	print("Done!!!")

