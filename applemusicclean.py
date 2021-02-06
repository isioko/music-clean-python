# import requests
# import json
# import math
# import jwt

# import applemusicpy

# from datetime import datetime, timedelta
# import time

# from flask import Flask, render_template, request, redirect, url_for, session, flash

# import secrets

# ALG = "ES256" # encryption algo that Apple requires
# SESSION_LEN = 1 # length Apple Music token is valid, in hours

# # am = applemusicpy.AppleMusic(secret_key=secrets.SECRET_KEY, key_id=secrets.KEY_ID, team_id=secrets.TEAM_ID)
# # results = am.search('travis scott', types=['albums'], limit=5)
# # for item in results['results']['albums']['data']:
# # 	print(item['attributes']['name'])

# def get_dev_token():
# 	"""
# 	Gets an encrypted token to be used by in API requests
# 	"""

# 	headers = {
# 		"alg": ALG,
# 		"kid": secrets.KEY_ID,
# 	}

# 	payload = {
# 		'iss': secrets.TEAM_ID,  # issuer
# 		'iat': int(datetime.now().timestamp()),  # issued at
# 		'exp': int((datetime.now() + timedelta(hours=SESSION_LEN)).timestamp()),  # expiration time
# 	}

# 	token = jwt.encode(payload, secrets.SECRET_KEY, algorithm=ALG, headers=headers)
# 	token_str = token.decode()

# 	return token_str
	
# 	# put token_str in session when ready


# def get_playlists():
# 	url = "https://api.music.apple.com/v1/me/library/playlists"

# 	response = requests.get(url)
# 	print(response.text)

# 	playlists = response.json()
# 	print(playlists.items)