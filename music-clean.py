import requests
import json
import math

import spotipy
import spotipy.util as util

from datetime import datetime

import secrets

class Playlists(object):
    def __init__(self, data):
	    self.__dict__ = json.loads(data)

def getToken(username):
	scope = 'playlist-read-private playlist-read-collaborative playlist-read-private playlist-modify-public playlist-modify-private'

	token = util.prompt_for_user_token(username, scope, client_id=secrets.CLIENT_ID, client_secret=secrets.CLIENT_SECRET, redirect_uri=secrets.REDIRECT_URI)

	return token

def getPlaylistsAPICall(username, token, limit, offset, playlists_dict):
	bearer_authorization = "Bearer " + token

	url = "https://api.spotify.com/v1/users/" + username + "/playlists"
	headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': bearer_authorization}

	params = {'limit': limit, 'offset': offset}

	r = requests.get(url, headers=headers, params=params)

	json_data = r.text
	playlists = Playlists(json_data) # fix this name to be more general 

	for playlist in playlists.items:
		playlists_dict[playlist['name']] = [playlist['id'], playlist['public']]
		print(playlist['name'])

	num_playlists = playlists.total

	return num_playlists, playlists_dict

def getPlaylists(username, token):
	playlists_dict = {}

	if token:
		print("Here are your playlists:")

		num_playlists_limit = 50
		num_playlists, playlists_dict = getPlaylistsAPICall(username, token, num_playlists_limit, 0, playlists_dict)

		num_addtl_playlists_calls = math.ceil(num_playlists / num_playlists_limit) - 1

		for i in range(num_addtl_playlists_calls):
			offset = num_playlists_limit + (num_playlists_limit * i)
			_, playlists_dict = getPlaylistsAPICall(username, token, num_playlists_limit, offset, playlists_dict)
	else:
		print("Invalid token for", username)
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
		print("Invalid token for", username)
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

	print("Could not find the clean version of " + search_track_name + " :(")
	
	return None

def searchForCleanTracks(username, token, explicit_tracks):
	search_tracks_uris = ""

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
			search_tracks_uris += clean_track_uri + ","

	return search_tracks_uris

# Maybe change to filter tracks 
# TO DO: Update so that more than XX tracks
def getExplicitTracks(username, token, playlist_name, playlist_id, clean_playlist_id, playlist_public):
	explicit_tracks_dict = {}
	
	bearer_authorization = "Bearer " + token

	if token:
		print("Here are the tracks in " + playlist_name + ":")

		url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks"
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': bearer_authorization}
		r = requests.get(url, headers=headers)

		json_data = r.text
		tracks = Playlists(json_data) # fix this name to be more general 

		explicit_tracks = [] # list of [track name, [track artists]]
		clean_tracks_uris = ""

		for track in tracks.items:
			print(track['track']['name'])
			if track['track']['explicit']:
				track_artists = getTrackArtists(track['track']['artists'])
				explicit_tracks.append([track['track']['name'], track_artists])
			else:
				clean_tracks_uris += track['track']['uri'] + ","
		
		print("")

		search_tracks_uris = searchForCleanTracks(username, token, explicit_tracks)
		all_tracks_uris = clean_tracks_uris + search_tracks_uris

		# TO DO: check for 100 track limit
		addTracksToPlaylist(username, token, clean_playlist_id, all_tracks_uris, playlist_public)
	else:
		print("Invalid token for", username)
		# Need to throw error here 

	return explicit_tracks_dict

def main():
	print("Welcome to music clean! We'll make sure any of your Spotify playlists are clean for whe you need them.")
	print("")

	username = input("What is your Spotify username? ")
	print("")

	token = getToken(username)

	playlists_dict = getPlaylists(username, token)

	print("")

	playlist_to_clean = input("Type the name of the playlist to clean: ")
	while checkIfValidPlaylist(playlist_to_clean, playlists_dict) is False:
		print("Oops! Invalid playlist. Please try again.")
		playlist_to_clean = input("Type the name of the playlist to clean: ")

	print("")
	print("Time to clean " + playlist_to_clean + ". Hang tight!")
	print("")

	clean_playlist_id = createPlaylist(username, token, playlist_to_clean)

	getExplicitTracks(username, token, playlist_to_clean, playlists_dict[playlist_to_clean][0], clean_playlist_id, playlists_dict[playlist_to_clean][1])

	print("")
	print("Congrats! We added a cleaned " + playlist_to_clean + " playlist with the clean songs we could find to your Spotify account. Enjoy :)")
	  
if __name__== "__main__":
	main()