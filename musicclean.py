import requests
import json
import math

import spotipy
import spotipy.util as util

from datetime import datetime
from urllib.request import urlopen

import six
import six.moves.urllib.parse as urllibparse

import secrets

NUM_PLAYLISTS_LIMIT = 50
NUM_TRACKS_LIMIT = 100


def get_authorize_url():
    """ Gets the URL to use to authorize this app
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

def getToken(username):
	scope = 'playlist-read-private playlist-read-collaborative playlist-read-private playlist-modify-public playlist-modify-private user-read-email user-read-private'

	url = "https://accounts.spotify.com/authorize"
	params = {'client_id': secrets.CLIENT_ID, 'reponse_type': 'code', 'redirect_uri': secrets.REDIRECT_URI, 'scope': scope}

	r = requests.get(get_authorize_url())

def getPlaylistsAPICall(username, token, offset, playlists_dict):
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

def getPlaylists(username, token):
	playlists_dict = {}

	if token:
		num_playlists, playlists_dict = getPlaylistsAPICall(username, token, 0, playlists_dict)

		num_addtl_playlists_calls = math.ceil(num_playlists / NUM_PLAYLISTS_LIMIT) - 1

		for i in range(num_addtl_playlists_calls):
			offset = NUM_PLAYLISTS_LIMIT + (NUM_PLAYLISTS_LIMIT * i)
			_, playlists_dict = getPlaylistsAPICall(username, token, offset, playlists_dict)
	else:
		print(">> Invalid token for", username)
		# Need to throw error here 

	return playlists_dict

def checkIfValidPlaylist(playlist_to_clean, playlists_dict):
	if playlist_to_clean in playlists_dict:
		return True
	else:
		return False

def createPlaylist(username, token, playlist_to_clean):
	new_playlist_name = playlist_to_clean + " CLEANED " + str(datetime.now())

	sp = spotipy.Spotify(auth=token)
	result = sp.user_playlist_create(username, new_playlist_name, public=False, description='')

	return result['id']

def addTracksToPlaylist(username, token, playlist_id, track_uris, playlist_public):
	bearer_authorization = "Bearer " + token

	if token:
		url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks"
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': bearer_authorization}
		params = {'uris': track_uris}
		r = requests.post(url, headers=headers, params=params) 

		# TO DO: add a check to see if the addition was successful
	else:
		print(">> Invalid token for", username)
		# Need to throw error here

def getTrackArtists(artists_json):
	artists = []
	for artist in artists_json:
		artists.append(artist['name'])

	return artists

def checkSearchResultForCleanTrack(result_tracks, search_track_name, search_track_artists):
	for result_track in result_tracks:
		result_track_artists = set(getTrackArtists(result_track['artists']))
		if result_track['name'] == search_track_name and set(search_track_artists) == result_track_artists and result_track['explicit'] == False:
			return result_track['uri']
	
	return None

def searchForCleanTracks(username, token, explicit_tracks, could_not_clean_tracks):
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

		clean_track_uri = checkSearchResultForCleanTrack(search_result['tracks']['items'], track_name, track_artists)

		if clean_track_uri != None:
			search_tracks_uris.append(clean_track_uri)
		else:
			could_not_clean_tracks.append(track_name)

	return search_tracks_uris, could_not_clean_tracks

def getPlaylistTracksAPICall(username, token, playlist_id, offset):
	bearer_authorization = "Bearer " + token

	url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks"
	headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': bearer_authorization}
	params = {'limit': NUM_TRACKS_LIMIT, 'offset': offset}
	r = requests.get(url, headers=headers, params=params)

	tracks = r.json()

	return tracks 

def filterTracks(tracks, explicit_tracks, clean_tracks_uris, all_tracks):
	for track in tracks["items"]:
		all_tracks.append(track['track']['name'])
		if track['track']['explicit']:
			track_artists = getTrackArtists(track['track']['artists'])
			explicit_tracks.append([track['track']['name'], track_artists])
		else:
			clean_tracks_uris.append(track['track']['uri'])

	return explicit_tracks, clean_tracks_uris, all_tracks

def convertTrackURIListToString(track_uris_list):
	track_uris = ""
	for uri in track_uris_list:
		track_uris += uri + ","

	return track_uris

def getTracks(username, token, playlist_name, playlist_id, clean_playlist_id, playlist_public):
	all_tracks = []
	could_not_clean_tracks = []

	explicit_tracks_dict = {}
	
	bearer_authorization = "Bearer " + token

	if token:
		explicit_tracks = [] # list of [track name, [track artists]]
		clean_tracks_uris = []

		tracks = getPlaylistTracksAPICall(username, token, playlist_id, 0)
		num_tracks = tracks["total"]

		explicit_tracks, clean_tracks_uris, all_tracks = filterTracks(tracks, explicit_tracks, clean_tracks_uris, all_tracks)

		num_addtl_tracks_calls = math.ceil(num_tracks / NUM_TRACKS_LIMIT) - 1
		for i in range(num_addtl_tracks_calls):
			offset = NUM_TRACKS_LIMIT + (NUM_TRACKS_LIMIT * i)
			tracks = getPlaylistTracksAPICall(username, token, playlist_id, offset)
			explicit_tracks, clean_tracks_uris, all_tracks = filterTracks(tracks, explicit_tracks, clean_tracks_uris, all_tracks)

		search_tracks_uris, could_not_clean_tracks = searchForCleanTracks(username, token, explicit_tracks, could_not_clean_tracks)
		all_tracks_uris = search_tracks_uris + clean_tracks_uris
		num_clean_tracks = len(all_tracks_uris)

		num_add_tracks_calls = math.ceil(num_tracks / NUM_TRACKS_LIMIT)
		for i in range(num_add_tracks_calls):
			if i == num_add_tracks_calls - 1:
				track_uris = convertTrackURIListToString(all_tracks_uris[i*NUM_TRACKS_LIMIT:])
			else:
				track_uris = convertTrackURIListToString(all_tracks_uris[i*NUM_TRACKS_LIMIT: (i*NUM_TRACKS_LIMIT) + NUM_TRACKS_LIMIT])

			addTracksToPlaylist(username, token, clean_playlist_id, track_uris, playlist_public)
	else:
		print(">> Invalid token for", username)
		# Need to throw error here 

	return explicit_tracks_dict, all_tracks, could_not_clean_tracks
