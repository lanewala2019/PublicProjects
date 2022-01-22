This project is licensed under the MIT License. The contents of this project
may be used freely under the terms of this license, with proper attribution
to the author.

The LEDBanners project contains scripts used to control a set of individually-
addressable LEDs.

The neopixel python library is used to control specific LEDs.  An array is
used to allow individual LEDs to be addressed (and thus controlled) using the
neopixel library.  So at the heart of this project we have an array that
contains elements that must be marked as on or off using RGB colors to indicate
that state.  The color value for each LED is simply an RGB value represented
as (0-255, 0-255, 0-255).  NOTE that these LED strands are in many cases set
up as GRB and not RGB, therefore one must ensure that the proper values are
being set.

The basic process of controlling these LEDs is simple -
- create pixels array using thge neopixel library
- set values of individual elements of the neopixels array as needed, simply
by using statements such as pixles[index] = (G, R, B)
- pixels.show() to push the LEDs to update their state

The pixels array is linear, whereas tghe physical LEDs are arranged in an 
8x50 grid.  Thus, the appropriate LEDs must be used in order to render a
character.

The complexity arises in transforming text banner data into the appropriate
set of LEDs that must be turned on/off.  Each character that must be scrolled
is transformed into an 8x5 grid of "dots", with the appropriate LEDs being
set as needed based on the dots that represent each character.

Thus, the text that is to be scrolled must be represented as a set of "dots".
This is done by indexing into a "fonts" array that contains the 8x5
representation of each character.  IN order to do that, a "source" array of
"dots" is used to hold the details of each "dot".  Appropriate information
on each "dot" is copied into the pixels array so that the neopixel library can
control the LEDs.  Once a set of "dots" has been rendered, all elements of
the pixels array are shifted left to simulate the scroll.  The next set of
"dots" is then introduced into the pixels array, and the process repeats.

