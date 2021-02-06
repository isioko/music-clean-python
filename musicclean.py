import requests
import json
import math
import base64

import spotipy
import spotipy.util as util

from datetime import datetime
from urllib.request import urlopen

import six
import six.moves.urllib.parse as urllibparse

from flask import Flask, render_template, request, redirect, url_for, session, flash

import secrets

NUM_PLAYLISTS_LIMIT = 50
NUM_TRACKS_LIMIT = 100

"""
SPOTIFY AUTHORIZATION AND TOKEN RETRIEVAL
"""

def get_authorize_url():
    """ 
    Gets the URL to use to authorize this app

    returns: authorization url string 
    """
    
    scope = 'playlist-read-private playlist-read-collaborative playlist-read-private playlist-modify-public playlist-modify-private'

    payload = {
        "client_id": secrets.CLIENT_ID,
        "response_type": "code",
        "redirect_uri": secrets.REDIRECT_URI,
        "scope": scope
    }

    urlparams = urllibparse.urlencode(payload)

    return "%s?%s" % ("https://accounts.spotify.com/authorize", urlparams)


def make_authorization_headers(client_id, client_secret):
	""" 
    Create authorization header for token request from Spotify API 

    param client_id: app id received to interact with Spotify API 
    param client_secret: app secret received to interact with Spotify API

    returns: dictionary with authorization header
    """

	auth_str = client_id + ":" + client_secret
	auth_header = base64.b64encode(auth_str.encode('ascii'))
	return {"Authorization": "Basic %s" % auth_header.decode('ascii')}


def get_token(code):
	"""
	Retrieves authorization token from Spotify and stores it in Flask session

	param code: authorization code received from Spotify 
	"""

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
	else:
		print("Error retrieving token")


def get_username():	
	"""
	Retrieves user's Spotify username and stores it in Flask session
	"""
	headers = {
		"Authorization": "Bearer " + session.get("token"),
	}

	url = "https://api.spotify.com/v1/me"

	response = requests.get(url, headers=headers)
	if response.status_code == 200:
		user = response.json()
		session["username"] = user["id"]
	else:
		print("Error retrieving username")


"""
GET USER'S SPOTIFY PLAYLISTS
"""

def get_playlists_api_call(username, token, offset, playlists_dict):
	"""
	Makes call to Spotify API to get NUM_PLAYLISTS_LIMIT number of playlists from user's account

	param username: user's Spotify name
	param token: Spotify authorization token for user
	param offset: the index of the first playlist to return	
	param playlists_dict: dictionary of user's playlists (key: playlist id and value: playlist name)

	returns: num_playlists - total # of playlists, playlists_dict - dictionary of user's playlists (key: playlist id and value: playlist name)
	"""

	bearer_authorization = "Bearer " + token

	url = "https://api.spotify.com/v1/users/" + username + "/playlists"
	headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': bearer_authorization}

	params = {'limit': NUM_PLAYLISTS_LIMIT, 'offset': offset}

	r = requests.get(url, headers=headers, params=params)

	playlists = r.json()
	print(playlists.items)

	for playlist in playlists["items"]:
		playlists_dict[playlist['id']] = playlist['name']

	num_playlists = playlists["total"]

	return num_playlists, playlists_dict


def get_playlists(username, token):
	"""
	Gets all of a user's Spotify playlists

	param username: user's Spotify name
	param token: Spotify authorization token for user

	returns: playlists_dict - dictionary of user's playlists (key: playlist id and value: playlist name)
	"""

	playlists_dict = {}

	num_playlists, playlists_dict = get_playlists_api_call(username, token, 0, playlists_dict)

	num_addtl_playlists_calls = math.ceil(num_playlists / NUM_PLAYLISTS_LIMIT) - 1

	for i in range(num_addtl_playlists_calls):
		offset = NUM_PLAYLISTS_LIMIT + (NUM_PLAYLISTS_LIMIT * i)
		_, playlists_dict = get_playlists_api_call(username, token, offset, playlists_dict)

	return playlists_dict


"""
CREATE EMPTY SPOTIFY PLAYLIST 
"""

def create_playlist(username, token, playlist_to_clean):
	"""
	Creates empty Spotify playlist to store clean songs

	param username: user's Spotify username
	param token: Spotify authorization token for user
	param playlist_to_clean: name of user's Spotify playlist to clean

	returns: id of newly created Spotify playlist
	"""

	curr_date_time = datetime.now()
	curr_date_time = curr_date_time.strftime("%x")

	new_playlist_name = "[clean] " + playlist_to_clean + " " + curr_date_time

	sp = spotipy.Spotify(auth=token)
	response = sp.user_playlist_create(username, new_playlist_name, public=False, description='')

	return response['id']


"""
GET USER TRACKS AND ADD CLEAN TRACKS TO NEW PLAYLIST
"""

def add_tracks_to_playlist(username, token, playlist_id, track_uris):
	"""
	Adds tracks to Spotify playlist 

	param username: user's Spotify username
	param token: Spotify authorization token for user
	param playlist_id: id of new clean Spotify playlist
	param track_uris: list of Spotify track URIs to add to the playlist
	"""

	bearer_authorization = "Bearer " + token
	url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks"
	headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': bearer_authorization}
	params = {'uris': track_uris}

	response = requests.post(url, headers=headers, params=params) 


def get_track_artists(artists_json):
	"""
	Returns set of track's artist names from request's JSON response

	param artists_json: JSON response with Spotify Artist objects
	
	returns: list of artist names 
	"""

	artists = []
	for artist in artists_json:
		artists.append(artist['name'])

	return artists


def check_search_result_for_clean_track(result_tracks, search_track_name, search_track_artists):
	"""
	Locates clean version of a track from the search results JSON

	param result_tracks: JSON response with Spotify Track objects from search for track
	param search_track_name: name of track to locate
	param search_track_artists: artists on track to locate
	
	returns: URI of clean track if found or None 
	"""

	for result_track in result_tracks:
		result_track_artists = set(get_track_artists(result_track['artists']))
		if result_track['name'] == search_track_name and set(search_track_artists) == result_track_artists and result_track['explicit'] == False:
			return result_track['uri']
	
	return None


def search_for_clean_tracks(username, token, explicit_tracks, could_not_clean_tracks):
	"""
	Searches for clean version of explicit tracks

	param username: user's Spotify name
	param token: Spotify authorization token for user
	param explicit_tracks: list of [track name, [track artists]] for explicit tracks 
	param could_not_clean_tracks: list of track names for which a clean version could not be found

	returns: search_track_uris - track URIs for clean version of tracks, could_not_clean_tracks - list of tracks for which a clean version could not be found
	"""

	search_tracks_uris = []

	for track in explicit_tracks:
		track_name = track[0]
		track_artists = track[1]

		track_artists_str = ""
		for artist in track_artists:
			track_artists_str += artist + ","

		sp = spotipy.Spotify(auth=token)
		q = "track:\"" + track_name + "\" artist:" + track_artists[0]
		search_result = sp.search(q)

		clean_track_uri = check_search_result_for_clean_track(search_result['tracks']['items'], track_name, track_artists)

		if clean_track_uri != None:
			search_tracks_uris.append(clean_track_uri)
		else:
			could_not_clean_tracks.append(track_name)

	return search_tracks_uris, could_not_clean_tracks


def get_playlist_tracks_api_call(username, token, playlist_id, offset):
	"""
	Makes call to Spotify API to get NUM_TRACKS_LIMIT number of tracks from user's playlist

	param username: user's Spotify name
	param token: Spotify authorization token for user
	param playlist_id: id of playlist to get tracks from
	param offset: the index of the first track to return	

	returns: JSON object of Spotify Track objects
	"""

	bearer_authorization = "Bearer " + token

	url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks"
	headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': bearer_authorization}
	params = {'limit': NUM_TRACKS_LIMIT, 'offset': offset}
	response = requests.get(url, headers=headers, params=params)

	tracks = response.json()

	return tracks 


def filter_tracks(tracks, explicit_tracks, clean_tracks_uris, all_tracks):
	"""
	Separates clean and explicit tracks from JSON tracks response

	param tracks: JSON object with Spotify Track objects from playlist to add to other params
	param explicit_tracks: list of exisiting [track name, [track artists]]
	param clean_tracks_uris: list of existing clean track URIs (strings)
	param all_tracks: list of existing track names in playlist	

	returns: explicit_tracks - list of [track name, [track artists]], clean_tracks_uris - list of clean track URIs (strings), all_tracks - list of all the track names in playlist
	"""

	for track in tracks["items"]:
		all_tracks.append(track['track']['name'])
		if track['track']['explicit']:
			track_artists = get_track_artists(track['track']['artists'])
			explicit_tracks.append([track['track']['name'], track_artists])
		else:
			clean_tracks_uris.append(track['track']['uri'])

	return explicit_tracks, clean_tracks_uris, all_tracks


def convert_track_uri_list_to_string(track_uris_list):
	"""
	Converts list of track URIs to a comma-separated string

	param track_uris_list: list of track URIs

	returns: comma-separated string of the track URIs in track_uris_lists
	"""

	track_uris = ""
	for uri in track_uris_list:
		track_uris += uri + ","

	return track_uris


def get_tracks(username, token, playlist_name, playlist_id, clean_playlist_id):
	all_tracks = []
	could_not_clean_tracks = []

	explicit_tracks_dict = {}
	
	explicit_tracks = [] # list of [track name, [track artists]]
	clean_tracks_uris = []

	# get all tracks in playlist - separate by clean vs. explicit

	tracks = get_playlist_tracks_api_call(username, token, playlist_id, 0)
	num_tracks = tracks["total"]

	explicit_tracks, clean_tracks_uris, all_tracks = filter_tracks(tracks, explicit_tracks, clean_tracks_uris, all_tracks)

	num_addtl_tracks_calls = math.ceil(num_tracks / NUM_TRACKS_LIMIT) - 1
	for i in range(num_addtl_tracks_calls):
		offset = NUM_TRACKS_LIMIT + (NUM_TRACKS_LIMIT * i)
		tracks = get_playlist_tracks_api_call(username, token, playlist_id, offset)
		explicit_tracks, clean_tracks_uris, all_tracks = filter_tracks(tracks, explicit_tracks, clean_tracks_uris, all_tracks)

	# search for clean version of explicit tracks

	search_tracks_uris, could_not_clean_tracks = search_for_clean_tracks(username, token, explicit_tracks, could_not_clean_tracks)
	all_tracks_uris = search_tracks_uris + clean_tracks_uris
	num_clean_tracks = len(all_tracks_uris)

	# add all tracks to new, cleaned playlist
	
	num_add_tracks_calls = math.ceil(num_tracks / NUM_TRACKS_LIMIT)
	for i in range(num_add_tracks_calls):
		if i == num_add_tracks_calls - 1:
			track_uris = convert_track_uri_list_to_string(all_tracks_uris[i*NUM_TRACKS_LIMIT:])
		else:
			track_uris = convert_track_uri_list_to_string(all_tracks_uris[i*NUM_TRACKS_LIMIT: (i*NUM_TRACKS_LIMIT) + NUM_TRACKS_LIMIT])

		add_tracks_to_playlist(username, token, clean_playlist_id, track_uris)

	return explicit_tracks_dict, all_tracks, could_not_clean_tracks



