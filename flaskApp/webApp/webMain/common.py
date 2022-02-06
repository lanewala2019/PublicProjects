#
# A set of commonly-used properties, so just include these in every script 
#
import os

APP_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(APP_PATH, 'templates/')
RESOURCE_PATH = os.path.join(APP_PATH, 'resources/')
BANNER_PATH = os.path.join(RESOURCE_PATH, 'banners/')

# This is the port to use (How the webapp is used)
APP_PORT = '5011'

HOME_TEMPLATE = 'home.html'
ABOUT_TEMPLATE = 'about.html'
BANNER_TEMPLATE = 'banner.html'
CONTACT_TEMPLATE = 'contact.html'
CREATE_TEMPLATE = 'create.html'

LEDLIGHT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))+'/LEDBanners/'
SCROLLINGLED_PROGRAM = 'ScrollingLEDs.py'
TMP_PATH = os.path.join(APP_PATH, 'tmp/')
#
# REPLACE: YOUTUBE <CHANNEL_ID> WITH YOUR OWN
VIDEOINNERHTML = '<iframe width="424" height="240" src="https://www.youtube.com/embed/live_stream?channel=<CHANNEL_ID>&autoplay=1" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'

# Okta-related
#
# OKTADOMAIN = assigned when an Okta developer acct is created
# SECRETKEY = any key you create (or have a way to generate) that is unique to you
# OKTAAUTHTOKEN = generated from the Okta developer portal
#                   - navigate to Security->API->Tokens->Create Token
SECRETKEY = '<A_SECRET_KEY>'
OKTADOMAIN = "https://<YOUR_OKTA_DOMAIN>.okta.com"
OKTAAUTHTOKEN = "<YOUR_OKTA_AUTH_TOKEN>"
