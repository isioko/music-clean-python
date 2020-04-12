import os
from flask import Flask, render_template, request, redirect, url_for, session
import requests 
import base64 
import time

import musicclean
import secrets
import classes

app = Flask(__name__)
app.secret_key = "isiokoisi"
SESSION_TYPE = 'redis'

clean = classes.MusicClean()
user_playlists = classes.Playlists()

debug = True

def startup():
	clean.reset()
	user_playlists.reset()

@app.route("/", methods=["GET", "POST"])
def start():
	if request.method == "GET":
		startup()
		session["token"] = None
		session["username"] = None

		if debug:
			print("ROUTE: START")
			print("USERNAME (should be None):", session.get("username"))
			print("TOKEN (should be None):", session.get("token"))
			# print("PLAYLISTS (should be []):", user_playlists.playlists_list)

		return render_template("home.html", auth_url=musicclean.get_authorize_url())

def is_token_expired(token_info):
    now = int(time.time())
    return token_info["expires_in"] - now < 60

def make_authorization_headers(client_id, client_secret):
	auth_str = client_id + ":" + client_secret
	auth_header = base64.b64encode(auth_str.encode('ascii'))
	return {"Authorization": "Basic %s" % auth_header.decode('ascii')}

def getToken(code):
	payload = {
		"redirect_uri": secrets.REDIRECT_URI,
		"code": code,
		"grant_type": "authorization_code"
	}

	headers = make_authorization_headers(secrets.CLIENT_ID, secrets.CLIENT_SECRET)
	url = "https://accounts.spotify.com/api/token"

	response = requests.post(url, data=payload, headers=headers)
	if response.status_code == 200:
		token_info = response.json()
		token = token_info['access_token']

		session["token"] = token
		session["token_info"] = token_info
		
		# clean.setToken(token)
		# clean.setTokenInfo(token_info)
	else:
		print("Error retrieving token")


@app.route("/playlists/", methods=["GET", "POST"])
def playlists():
	if request.method == "GET":
		playlists_dict = musicclean.getPlaylists(session.get("username"), session.get("token"))
		session["playlists_dict"] = playlists_dict
		# user_playlists.setPlaylistsDict(playlists_dict)

		playlists_list = []
		for playlist in playlists_dict:
			playlists_list.append(playlist)

		session["playlists_list"] = playlists_list
		session["num_playlists"] = len(playlists_list)	
		# user_playlists.setPlaylistsList(playlists_list)
		# user_playlists.setNumPlaylists(len(playlists_list))

		if debug:
			print("ROUTE: PLAYLISTS GET")
			# print("playlists_dict", user_playlists.playlists_dict, "playlists_list", user_playlists.playlists_list, "num_playlists", user_playlists.num_playlists)
		
		return render_template("playlists.html", playlists=playlists_list)

	if request.method == "POST":
		if debug:
			print("ROUTE: PLAYLISTS POST")
			# print("playlists_dict", user_playlists.playlists_dict, "playlists_list", user_playlists.playlists_list, "num_playlists", user_playlists.num_playlists)
			# print("playlist_to_clean_num", playlist_to_clean_num)
		
		playlist_to_clean_num = int(request.form['playlistToClean']) # need to check if can be converted to int
		
		if session.get("playlists_list") is not None:
			playlists_list = session.get("playlists_list")
			playlist_to_clean_name = playlists_list[playlist_to_clean_num-1]
		else:
			# throw error
			playlist_to_clean_name = None

		if session.get("playlists_dict") is not None:
			playlists_dict = session.get("playlists_dict")
			playlists_list = session.get("playlists_list")
			playlist_to_clean_id = playlists_dict[playlists_list[playlist_to_clean_num-1]][0]
		else:
			# throw error
			playlist_to_clean_id = None

		session["playlist_to_clean_num"] = playlist_to_clean_num
		session["playlist_to_clean_name"] = playlist_to_clean_name
		session["playlist_to_clean_id"] = playlist_to_clean_id

		# user_playlists.setPlaylistToCleanNum(playlist_to_clean_num)
		# user_playlists.setPlaylistToCleanID(user_playlists.playlists_dict[user_playlists.playlists_list[playlist_to_clean_num-1]][0])
		# user_playlists.setPlaylistToCleanName(playlist_to_clean_name)

		# clean_playlist_id = musicclean.createPlaylist(clean.username, clean.token, playlist_to_clean_name)
		# _, all_tracks, could_not_clean_tracks = musicclean.getTracks(clean.username, clean.token, playlist_to_clean_name, user_playlists.playlists_dict[playlist_to_clean_name][0], clean_playlist_id, user_playlists.playlists_dict[playlist_to_clean_name][1])
		# user_playlists.setAllTracks(all_tracks)
		# user_playlists.setCouldNotCleanTracks(could_not_clean_tracks)

		clean_playlist_id = musicclean.createPlaylist(session.get("username"), session.get("token"), playlist_to_clean_name)

		playlists_dict = session.get("playlists_dict")
		_, all_tracks, could_not_clean_tracks = musicclean.getTracks(session.get("username"), session.get("token"), playlist_to_clean_name, playlists_dict[playlist_to_clean_name][0], clean_playlist_id, playlists_dict[playlist_to_clean_name][1])
		session["all_tracks"] = all_tracks
		session["could_not_clean_tracks"] = could_not_clean_tracks

		return redirect(url_for('cleanedPlaylist'))

@app.route("/cleanedplaylist/", methods=["GET"])
def cleanedPlaylist():
	# return render_template("cleaned_playlist.html", playlistName=user_playlists.playlist_to_clean_name, allTracks=user_playlists.all_tracks, notCleanTracks=user_playlists.could_not_clean_tracks)
	playlist_to_clean_name = session.get("playlist_to_clean_name")
	all_tracks = session.get("all_tracks")
	could_not_clean_tracks = session.get("could_not_clean_tracks")

	return render_template("cleaned_playlist.html", playlistName=playlist_to_clean_name, allTracks=all_tracks, notCleanTracks=could_not_clean_tracks)


def getUsername():
	headers = {
		# "Authorization": "Bearer " + clean.token,
		"Authorization": "Bearer " + session.get("token"),
	}

	url = "https://api.spotify.com/v1/me"

	response = requests.get(url, headers=headers)
	if response.status_code == 200:
		user = response.json()
		session["username"] = user["id"]
		# clean.setUsername(user['id'])
	else:
		print("Error retrieving username")

@app.route("/callback/", methods=["GET"])
def callback():
	if debug:
		print("ROUTE: CALLBACK")

	# if clean.token is None:
	# if session.get("token") is None:
	getToken(request.args['code'])

	if debug:
		print("Got new token:", session.get("token"))

	#elif clean.token is not None and is_token_expired(clean.token_info):
	# elif session.get("token") is not None and is_token_expired(session.get("token_info")):
	# 	# refresh token here
	# 	print("need to refresh")

	# 	if debug:
	# 		print("Needed to refresh token")

	getUsername()

	if debug:
		print("Got username:", session.get("username"))

	return redirect(url_for('playlists'))

if __name__ == '__main__':
	app.run(debug=True)