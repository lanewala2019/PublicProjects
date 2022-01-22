# basic test - turn all 50 LEDs to green; wait 2 secs, turn all off
import board
import neopixel
from time import sleep

pixels = neopixel.NeoPixel(board.D18, 50, brightness=1)
pixels.fill((255,0,0))
pixels.show()
sleep(2)
pixels.fill((0,0,0))
