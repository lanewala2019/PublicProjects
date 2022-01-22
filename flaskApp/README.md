This project is licensed under the MIT License. The contents of this project
may be used freely under the terms of this license, with proper attribution
to the author.

The flaskApp web application project presents a front-end to the user that
allows one to create and "execute" a scrolling LED banner.

In order to allow interested persons to use this app, an Okta OpenID Connect
registration/authentication/authorization framework has been used.  The
webpages themselves use javascript quite liberally, so as to present a
useful visual appearance, e.g., the use of a dynamically-created table.

Banners are created using the "Create" menu item on the web app. A banner may be
one or more fragments of text with "attributes" such as color. Each fragment
is created as a separate table row. When completed, the set of fragments are
saved in a file on the server, and will be available for rendering using the 
"Banner" menu item.

The Banner menu item presents a table of the set of banner files found in a
folder on the server-side. Each file can be "rendered" using the "Run" icon,
and stopped using the "Stop" icon.  In order to view a running banner, a
YouTube stream is used to see the banner running.  Obviously you must set up
a YouTube streaming account in order to use this.  Details on how I set it up
are described elsewhere.

Because of limitations on using the Raspberry Pi libraries that control the
WS2811 LEDs, one and only one banner may be "run" at any one time.  The
banner is run by executing (as a subprocess) a scruipt in the LEDBanners
project.  Therefore I use the pid of the sub-process that is spawned to
keep track of any running banner, and the backing script ensures that only
one script runs at any one time.

More details of the LEDBanners project is available in that project's README.

