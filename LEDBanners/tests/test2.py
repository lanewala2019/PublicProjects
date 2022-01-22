# cycle through different colors for all 50 LEDs
import board
import neopixel
from time import sleep

pixels = neopixel.NeoPixel(board.D18, 50, brightness=1)
pixels.fill((0,0,0))
i = 0
j = 0
k = 0
for i in range (0, 255, 20):
	for j in range (0, 255, 20):
		for k in range (0, 255, 20):
			pixels.fill((i,j,k))
			pixels.show()

pixels.fill((0,0,0))
