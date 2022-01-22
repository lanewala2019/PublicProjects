import os
import sys
import re
from flask import Flask, render_template, flash, request, g, redirect, url_for
from wtforms import Form, StringField, TextAreaField, validators, SubmitField
import time
from webAppUtils import startSubProcess, stopSubProcess, createBannerFile
from webAppUtils import updateBannerPidInfo, resetBannerPidInfo, doesPidExist, anyOtherPidsExist
from common import * # template names, path names etc. that are common to more than one script
from flask_oidc import OpenIDConnect
from okta import UsersClient

sys.path.insert(0, "/home/pi/Projects/python/WordDictionary/")

from checkAcceptableWords import checkAcceptableWords


app=Flask(__name__) #instantiating flask object
app.config.from_object(__name__)
app.config['SECRET_KEY'] = SECRETKEY
app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json" # contains a bunch of configuration options for your unique app
app.config["OIDC_COOKIE_SECURE"] = False
app.config["OIDC_CALLBACK_ROUTE"] = "/oidc/callback"
app.config["OIDC_SCOPES"] = ["openid", "email", "profile"]
app.config["OIDC_ID_TOKEN_COOKIE_NAME"] = "oidc_token"
oidc = OpenIDConnect(app)
okta_client = UsersClient(OKTADOMAIN, OKTAAUTHTOKEN)


aggregateFilesContent = []


class ReusableForm(Form):

	@app.before_request
	def before_request():
		if oidc.user_loggedin:
			g.user = okta_client.get_user(oidc.user_getfield("sub"))
		else:
			g.user = None



	@app.route("/", methods=['POST', 'GET'])
	@app.route("/home", methods=['POST', 'GET'])
	def home():
		form = ReusableForm(request.form)

		if form.errors:
			print ("menus.py: Form errors",form.errors, " method=", request.method)

		return render_template(HOME_TEMPLATE, form=form)
	
	@app.route("/about/", methods=['POST', 'GET'])
	def about():
		return render_template(ABOUT_TEMPLATE)

	
	@app.route("/create/", methods=['POST', 'GET'])
	@oidc.require_login
	def create():
		data = None
		form = ReusableForm(request.form)

		if form.errors:
			print ("main.py: Form errors",form.errors, " method=", request.method)

		if request.method == 'POST':
			data = request.form.get('bannerContent')
			#print("main.py- data=",data)

			# check 'data' to ensure acceptable words
			# 'data' has colors as well, with the first piece the text
			myText = data.split("|")
			#print("create: myText=", myText)
			chkText = []
			for i in range(0, len(myText), 5):
				chkText.append(myText[i])
			# Now we have a list without the color fragments
			#print ("chkText = ", chkText)
			# create a string from the list first
			myTextStr = " ".join(str(el) for el in chkText)
			# eliminate any non-alphanumeric character (reusing a variable here)
			chkText = re.split('\W+', myTextStr)
			# defensive! eliminate any null content in list
			chkText = list(filter(None, chkText))
			#print("create: chkText=", chkText)
			ret = checkAcceptableWords(chkText)

			# return value is a string containing unacceptable words, or an empty string
			#print("banners.py create(): ret=", ret)
			if len(ret) > 0:
				#print("found ret == None")
				flash("Caution! Unacceptable words found - "+ret)
			else:
				# "data" is a string with three "columns" of info:
				# banner-text, text-color, background-color
				# The concatenated string contains these three columns separated by "|"
				# Multiple sets of these columns are possible. These sets of three must be 
				# organized as lines, and written to a temp file (that's how a python script
				# is set up that will consume these data). The file will be stored in the
				# resources directory.
				#
				# Once the file has been created, a subprocess will kick off the python script
				# that manipulates a set of WS2811 LEDs.
				fileName = "text_"+str(time.time_ns())+".bannertext"
				filePath = BANNER_PATH+fileName
				createBannerFile(filePath, data)


				# Initially, data will be null, so the "All fields are required" message will render on
				# webpage; for subsequent iterations, we'll flash the data entered on the web page (just
				# as a confirmation of the data entered); this bit is not technically necessary
				if data != None:
					flash("Message: Banner file "+fileName+" created, with content from table")
				else:
					flash("All fields are required.")

		return render_template(CREATE_TEMPLATE, form=form)



	@app.route("/banner/", methods=['POST', 'GET'])
	@oidc.require_login
	def banner():
		global aggregateFilesContent

		files = os.listdir(BANNER_PATH)
		#print("banner: files=", files)
		if len(aggregateFilesContent) == 0:
			while files:
				# Each "row" in the contents array represents a table row rendered in HTML.
				# To maintain proepr state, certain bits must be preserved across the page rendering.
				# In order to know what banner is running, its pid must be captured (note the banner
				# process is a separate sub-process so we need to know ots pid)
				# Further, rather than clutter up the web page, only the currently-running banner
				# will have its video element displayed, & so we must capture that cell's visibility state
				#
				# After initialization, this array is passed back and forth between the HTML template and
				# the python scripts.
				#
				# When a banner is "run"/"stopped", a couple of functions in webAppUtils.py are used
				# to set/unset visibility of the video cell (via the contents[] array)
				content = [] # the content of a specific file in a list
				content.append("style=visibility:hidden") #initialize video cell visibility
				content.append("") #placeholder for process pid (when running as a sub-process)
				file = files.pop()
				with open(BANNER_PATH+file, "r") as f:
					txt = f.read()
				txt = txt.replace('\n', '<br>')
				# add filename to the list to render (without the .bannertext extension)
				file1 = file
				fileStr = file1[:file1.index(".bannertext")]
				content.append(fileStr) # 3rd element in a list is the filename without the extension
				# now append the file contents
				content.append(txt) # gather content of a specific file
				# finally, append this whole thing as a "row" to be rendered
				aggregateFilesContent.append(content) # gather content of all files
		#print("banner(): aggregateFilesContent=***",aggregateFilesContent,"***")

		return render_template(BANNER_TEMPLATE, filesContent=aggregateFilesContent)

	
	@app.route("/runBanner/<fileName>", methods=['POST','GET'])
	@oidc.require_login
	def runBanner(fileName):
		global aggregateFilesContent
		
		# If there is a pid for this, don't do anything, because it means something is already
		# running for this entry
		if (doesPidExist(fileName, aggregateFilesContent) == False):
			if (anyOtherPidsExist(aggregateFilesContent) == False):
				process = startSubProcess(fileName+".bannertext", process=None)
				# search for filename in aggregateFilesContent, and set aggregareFilesContent[idx-1] to 'process'
				# That's how we know which process to terminate when the appropriate link is clicked
				aggregateFilesContent = updateBannerPidInfo(fileName, str(process.pid), aggregateFilesContent)
				#print("runBanner(): aggregateFilesContent=***",aggregateFilesContent,"***")
			else:
				msg = "Sorry - there is another banner running. Stop that one first."
				#flash("Sorry - there is another banner running. Stop that one first.")
		else:
			msg = "Sorry. This banner is already running. You can have only one banner active"
			#flash("Sorry. This banner is already running. You can have only one banner active")
		return render_template(BANNER_TEMPLATE, filesContent=aggregateFilesContent)

	
	@app.route("/stopBanner/", defaults={'pid': None}, methods=['POST','GET'])
	@app.route("/stopBanner/<pid>/", methods=['POST','GET'])
	@oidc.require_login
	def stopBanner(pid):
		global aggregateFilesContent
		
		#print("stopBanner: pid=[", pid, "]")
		if (pid == None or pid == ''):
			pass
		else:
			stopSubProcess(int(pid))
			aggregateFilesContent = resetBannerPidInfo(pid, aggregateFilesContent)
			#print("stopBanner(): aggr=###",aggregateFilesContent,"###")
		return render_template(BANNER_TEMPLATE, filesContent=aggregateFilesContent)

	
	@app.route("/contact/", methods=['POST', 'GET'])
	def contact():
		return render_template(CONTACT_TEMPLATE)

	@app.route("/login")
	@oidc.require_login
	def login():
		return redirect(url_for("home"))

	@app.route("/logout")
	def logout():
		oidc.logout()
		return redirect(url_for("home"))


if __name__ == "__main__":
    app.run (host='0.0.0.0', port='5001')

