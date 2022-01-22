import board
import neopixel
from time import sleep

pixels = neopixel.NeoPixel(board.D18, 10, auto_write=False)

try:
	while (True):
		for led in range(0, len(pixels)):
			pixels[led] = (50, 0, 0)
		pixels.show()
		sleep(1)
		pixels.fill((255,0,0))
		pixels.show()
		sleep(1)
except KeyboardInterrupt:
	pixels.fill((0,0,0))
	pixels.show()
	
