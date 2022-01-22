import sys
import numpy
from fonts8x8 import font8x8 as f

x = 0xf0

def isBitSet(num, bit):
	return bool(num & 1 << bit -1)

for i in range (1,9):
	print(1 if isBitSet(x,i) else 0, end="," )
print()
