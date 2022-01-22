import board
import neopixel

pixels = neopixel.NeoPixel(board.D18, 500, brightness=1)
pixels.fill((0,0,0))
