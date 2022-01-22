This project is licensed under the MIT License. The contents of this project
may be used freely under the terms of this license, with proper attribution
to the author.

This repository contains three individual projects that are meant to be used
together, although the LEDBanners project may also be used independently.

Briefly, the repository content allows you to create and manage a set of
banners destined to be displayed using a grid of individually-addressable
LEDs.

The flaskApp project is a web application that allows you to create and
"run" specific banners. An Okta-based OpenID Connect registration/auth
framework allows you to restrict access to registered users. When a specific
banner is to be rendered, it executes scripts in the LEDBanners project.

The LEDBanners project specifically controls the set of LEDs by setting
relevant ones to a particular color and brightness. A fragment of text that
is to be rendered is converted into a set of 8x5 "dot-matrix" representations
suitable to control individual LEDs. I used a total of 400 LEDs (8 sets of
WS2811 LEDs, each a strand of 50).

From a hardware perspective, I used a Raspberry Pi 4 to drive the WS2811
LEDs. The 400 LEDs are powered using an external 12VDC supply so as to ensure
enough power for each LED. In addition, I used a Raspberry Pi Zero 2 W with a
Raspberry Pi NoIR camera so that a webapp user can see how the scrolling
banner appears.  Since I was using strands of WS2811 LEDs, I needed something
to mount the LEDs on a firmer surface and so I used a 12in x 36in x 1/8in
polycarbonate sheet into which I drilled 400 holes with a 7/16in acrylic drill
bit arranged in an appropriate grid.

Hope you enjoy.



