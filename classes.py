class MusicClean():
	def __init__(self):
		self.username = None
		self.token = None

	def setUsername(self, username):
		self.username = username

	def setToken(self, token):
		self.token = token

	def getUsername(self):
		return self.username

	def getToken(self):
		return self.token

class Playlists():
	def __init__(self):
		self.playlists_dict = {}
		self.playlists_list = []
		self.num_playlists = None
		self.playlist_to_clean_number = None
		self.playlist_to_clean_id = None
		self.playlist_to_clean_name = None
		self.all_tracks = []
		self.could_not_clean_tracks = []

	def setPlaylistsDict(self, playlists_dict):
		self.playlists_dict = playlists_dict

	def setPlaylistsList(self, playlists_list):
		self.playlists_list = playlists_list

	def setNumPlaylists(self, num_playlists):
		self.num_playlists = num_playlists

	def setPlaylistToCleanNum(self, playlist_to_clean_number):
		self.playlist_to_clean_number = playlist_to_clean_number

	def setPlaylistToCleanID(self, playlist_to_clean_id):
		self.playlist_to_clean_id = playlist_to_clean_id

	def setPlaylistToCleanName(self, playlist_to_clean_name):
		self.playlist_to_clean_name = playlist_to_clean_name

	def setAllTracks(self, all_tracks):
		self.all_tracks = all_tracks

	def setCouldNotCleanTracks(self, could_not_clean_tracks):
		self.could_not_clean_tracks = could_not_clean_tracks

	def isValidPlaylistNum(self, playlist_to_clean):
		if playlist_to_clean is int and playlist_to_clean > 0 and playlist_to_clean <= self.num_playlists:
			return True
		else:
			return False