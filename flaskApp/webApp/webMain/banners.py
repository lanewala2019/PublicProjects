import os
import sys
import re
from flask import Flask, render_template, flash, request, g, redirect, url_for
from wtforms import Form, StringField, TextAreaField, validators, SubmitField
import time
from webAppUtils import startSubProcess, stopSubProcess, createBannerFile, makeAggregateFilesContent
from webAppUtils import updateBannerPidInfo, resetBannerPidInfo, doesPidExist, anyOtherPidsExist
from common import * # template names, path names etc. that are common to more than one script
from flask_oidc import OpenIDConnect
from okta import UsersClient, UserGroupsClient

sys.path.insert(0, "/home/pi/Projects/python/WordDictionary/")

from checkAcceptableWords import checkAcceptableWords


# Most constants are defined in common.py
app=Flask(__name__) #instantiating flask object
app.config.from_object(__name__)

# Okta is used for authen/author using OpenID Connect
app.config['SECRET_KEY'] = SECRETKEY
app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json" # contains a bunch of configuration options for your unique app
app.config["OIDC_COOKIE_SECURE"] = False
app.config["OIDC_CALLBACK_ROUTE"] = "/oidc/callback"
app.config["OIDC_SCOPES"] = ["openid", "email", "profile"]
app.config["OIDC_ID_TOKEN_COOKIE_NAME"] = "oidc_token"
oidc = OpenIDConnect(app)
okta_client = UsersClient(OKTADOMAIN, OKTAAUTHTOKEN)
okta_groups = UserGroupsClient(OKTADOMAIN, OKTAAUTHTOKEN)


aggregateFilesContent = []


class ReusableForm(Form):

	# Okta authenticates/authorizes a client and manages appropriate session information.
	# Each authenticated user (whether explicitly registered with Okta or through Google)
	# is associated with a user id.
	@app.before_request
	def before_request():
		if oidc.user_loggedin:
			g.user = okta_client.get_user(oidc.user_getfield("sub"))
			#print ("before_request(): g.user.profile.firstName = [", g.user.profile.firstName,"]")
			#print ("before_request(): g.user.id = [", g.user.id,"]")
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

	

	# This manages the creation of a new banner. ONly authenticated users are permitted to create.
	# That authentication is managed by Pkta and OpenID Connect (the @oidc.require_login)
	@app.route("/create/", methods=['POST', 'GET'])
	@oidc.require_login
	def create():
		#print("In create(): g.user.id=[", g.user.id,"]")
		data = None
		form = ReusableForm(request.form)

		if form.errors:
			print ("main.py: Form errors",form.errors, " method=", request.method)

		if request.method == 'POST':
			data = request.form.get('bannerContent')
			#print("main.py- data=",data)

			# first element is the user id of the user who created this banner
			# We'll use that id as part of the filename. Embedding the user id into the
			# filename will be used to ensure that file deletions can happen only
			# by the appropriate user.

			uid = data[0:data.index("|")]
			data = data[data.index("|")+1:]
			#print("create(): uid=[",uid,"]")
			#print("create(): data=[",data,"]")

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
				fileName = uid+"_"+str(int(time.time()))+".bannertext"
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


	# Presents a list of existing banners thayt can be "run" by an authenticated user. Since there
	# may have been banner files deleted durign this session, the banner-file store is examined to ensure
	# that the correct list of files is presented
	@app.route("/banner/", methods=['POST', 'GET'])
	@oidc.require_login
	def banner():
		global aggregateFilesContent

		form = ReusableForm(request.form)

		aggregateFilesContent = makeAggregateFilesContent()
		return render_template(BANNER_TEMPLATE, filesContent=aggregateFilesContent, form=form)

	

	# This actually runs a selected banner file. Because of limitations on the use of GPIO
	# on the Raspberry Pi that controls the WS2811, only one banner can be run at any one time.
	# The list of banners is examined to ensure that no other banner is being run.
	# The "aggregateFilesContent" is a structure that maintains the list of banners along with
	# current state information, i.e., banner running or not.
	@app.route("/runBanner/<fileName>", methods=['POST','GET'])
	@oidc.require_login
	def runBanner(fileName):
		global aggregateFilesContent

		form = ReusableForm(request.form)
		
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
				flash("Sorry - there is another banner running. Stop that one first.")
		else:
			flash("Sorry. This banner is already running. You can have only one banner active")
		return render_template(BANNER_TEMPLATE, filesContent=aggregateFilesContent, form=form)

	

	# A running banner can be stopped.  A running banner is identified by a process id. A check is made
	# to ensure that there is a pid present before a stop is effected.
	@app.route("/stopBanner/", defaults={'pid': None}, methods=['POST','GET'])
	@app.route("/stopBanner/<pid>/", methods=['POST','GET'])
	@oidc.require_login
	def stopBanner(pid):
		global aggregateFilesContent

		form = ReusableForm(request.form)
		
		#print("stopBanner: pid=[", pid, "]")
		if (pid == None or pid == ''):
			pass
		else:
			stopSubProcess(int(pid))
			aggregateFilesContent = resetBannerPidInfo(pid, aggregateFilesContent)
			#print("stopBanner(): aggr=###",aggregateFilesContent,"###")
		return render_template(BANNER_TEMPLATE, filesContent=aggregateFilesContent, form=form)



	# A banner file can be deleted, but only by the creator that banner. This is done by using
	# the current user's user-id (provided through Okta) and matching that against a portion of
	# the banner filename.
	@app.route("/deleteBannerFile/<fileName>/", methods=['POST','GET'])
	@oidc.require_login
	def deleteBannerFile(fileName):
		global aggregateFilesContent

		form = ReusableForm(request.form)

		#
		# deleteBannerFile deletes a banner file if created by the logged-in user. The prefix of the
		# file is the user-id, and this will be used to determine if that file can be deleted or not.
		# After deletion, the list "aggregateFilesContent" must be adjusted to remove the file entry
		# from that list.

		fileCreator = fileName[0:fileName.index("_")]
		#print("deleteBannerFile(): fileCreator=[",fileCreator,"], g.user.id=[",g.user.id,"]")
		fileToDelete = fileName+".bannertext"
		#print("deleteBannerFile(): fileToDelete=[",fileToDelete,"]")

		if fileCreator == g.user.id:
			cmdToExecute = "sudo rm "+BANNER_PATH+fileToDelete
			os.system(cmdToExecute)

			# Re-do the banner files list
			aggregateFilesContent = makeAggregateFilesContent()

			flash("The banner "+fileName+" has been deleted.")
		else:
			flash("Sorry. The banner "+fileName+" was not created by you, and cannot be deleted.")
			
		return render_template(BANNER_TEMPLATE, filesContent=aggregateFilesContent, form=form)



	@app.route("/contact/", methods=['POST', 'GET'])
	def contact():
		return render_template(CONTACT_TEMPLATE)


	# Standard usage of Okta with Flask... The commented-out stuff is there just for any additional
	# information that one light wish to examine.
	@app.route("/login")
	@oidc.require_login
	def login():
		#users = okta_client.get_users()
		#print("/login: user Info=[", users, "]")
		#usr1 = users[0]
		#usr2 = users[1]
		#print("/login: user 1=[", dir(usr1.profile),"]")
		#print("/login: user 2=[", dir(usr2),"]")
		#groups = okta_groups.get_groups()
		#print("/login: group Info=[", dir(groups), "]")
		return redirect(url_for("home"))


	# Standard Okta/Flask artifact.  Note that logging-out deosn't eliminate your session
	# information right away. SO if you log back in again, Okta will validate your session
	# info and return an OK, which will take you right back to the app's home page.
	@app.route("/logout")
	def logout():
		oidc.logout()
		return redirect(url_for("home"))


# APP_PORT is defined in common.py
if __name__ == "__main__":
    app.run (host='0.0.0.0', port=APP_PORT)

