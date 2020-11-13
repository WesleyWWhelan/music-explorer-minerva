import json
from flask import Flask, request, redirect, g, render_template,url_for
import requests
from six.moves.urllib.parse import quote
from pandas.io.json import json_normalize
from flask_bootstrap import Bootstrap
from forms import SearchForm

##### Defintions #####

CLIENT_ID = 'f063991e203144ed94d9607e907b99cb'
CLIENT_SECRET = 
app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = 'something'

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
#CLIENT_SIDE_URL = "https://music-explorer-new.herokuapp.com/"
CLIENT_SIDE_URL = "http://127.0.0.1:8080"

REDIRECT_URI = "http://127.0.0.1:8080/callback/q"
#REDIRECT_URI = "https://music-explorer-new.herokuapp.com/callback/q"

REDIRECT_URI2 = "https://music-explorer-new.herokuapp.com/search"
SCOPE = "user-library-read user-top-read user-read-currently-playing user-read-playback-state user-follow-read user-read-recently-played streaming user-read-email user-read-private"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

#Endpoints:
GET_ARTIST_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'artists')
USER_PROFILE_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'me')
USER_RECENTLY_PLAYED_ENDPOINT = "{}/{}/{}".format(USER_PROFILE_ENDPOINT, 'player', 'recently-played')
USER_TOP_ARTISTS_ENDPOINT = "{}/{}".format(USER_PROFILE_ENDPOINT, 'top')
USER_TOP_TRACKS_ENDPOINT = "{}/{}".format(USER_PROFILE_ENDPOINT, 'top')
SEARCH_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'search')
USER_CURRENTLY_PLAYING_ENDPOINT = "{}/{}/{}".format(USER_PROFILE_ENDPOINT, 'player', 'currently-playing')

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "redirect_uri2": REDIRECT_URI2,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

##############
##### FUNCTIONS ######

def search(search_type, name,auth_header):
    if search_type not in ['artist', 'track', 'album', 'playlist']:
        print('invalid type')
        return None
    myparams = {'type': search_type}
    myparams['q'] = name
    resp = requests.get(SEARCH_ENDPOINT, params=myparams, headers = auth_header)
    return resp.json()

def get_related_artists(artist_id):
    url = "{}/{id}/related-artists".format(GET_ARTIST_ENDPOINT, id=artist_id)
    resp = requests.get(url)
    return resp.json()

def get_users_recently_played(auth_header):
    url = USER_RECENTLY_PLAYED_ENDPOINT
    resp = requests.get(url, headers=auth_header)
    return resp.json()

def user_top_artists(auth_header):
    artists = 'artists'
    url = "{}/{}".format(USER_TOP_ARTISTS_ENDPOINT,artists)
    resp = requests.get(url, headers=auth_header)
    return resp.json()

def user_top_tracks(auth_header):
    tracks = 'tracks'
    url = "{}/{}".format(USER_TOP_TRACKS_ENDPOINT,tracks)
    resp = requests.get(url, headers=auth_header)
    return resp.json()

def get_users_currently_playing(auth_header):
    url = USER_CURRENTLY_PLAYING_ENDPOINT
    resp = requests.get(url, headers=auth_header)
    if resp.status_code == 204:
        return '1'
    else:
        return resp


##############


@app.route('/')
def index():
    return render_template('index.html')

@app.route("/auth")
def auth():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/spotipy")
@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)
    name = profile_data['display_name']
    # Combine profile and playlist data to display
    
    #### top artists ####
    top_artists = []
    images = []
    for artist in user_top_artists(authorization_header)['items']:
        artist_c = dict_class(**artist)
        image = artist_c.images[0]['url']
        images.append(image)
        top_artists.append(artist_c)
    length = len(top_artists)
    middle_index = length//2
    artists1 = top_artists[:middle_index]
    artists2 = top_artists[middle_index:]
    ''' artist_images1 = images[:5]
    artist_images2 = images[5:10]
    packed1 = zip(artist_images1,artists1)'''

    #### top tracks ####
    top_tracks = []
    for track in user_top_tracks(authorization_header)['items']:
        track_c = dict_class(**track)
        top_tracks.append(track_c)
    length = len(top_tracks)
    middle_index = length//2
    tracks1 = top_tracks[:middle_index]
    tracks2 = top_tracks[middle_index:]

    #### recently played ####
    recently_played = []
    for track in get_users_recently_played(authorization_header)['items']:
        track_c = dict_class(**track['track'])
        recently_played.append(track_c)
    length = len(recently_played)
    middle_index = length//2
    recently_played1 = recently_played[:middle_index]
    recently_played2 = recently_played[middle_index:]
    #### currently playing ####
    
    '''currently_playing_song = get_users_currently_playing(authorization_header).json()['item']

    if currently_playing_song == '1':
        currently_playing = "No song is currently playing"
    else:
        currently_playing = dict_class(**currently_playing_song)'''
    

    return render_template('spotipy.html',top_artists1=artists1,
                                          top_artists2=artists2,top_tracks1=tracks1,
                                          top_tracks2=tracks2,recently_played2=recently_played2,
                                          recently_played1=recently_played1)

@app.route('/profile', methods=['GET', 'POST'])
def profile():

    return render_template('test.html',name='hello')
    
    
@app.route('/search', methods = ['GET','POST'])
def search():
    # Auth Step 4: Requests refresh and access tokens
    form=SearchForm()
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI2,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    auth_header = {"Authorization": "Bearer {}".format(access_token)}

    if request.method == 'POST':
        typo = request.form['typo']
        q = request.form['q']
        results = []
        for res in search(search_type, q,auth_header)['items']:
            result = dict_class(**res)
            results.append(result)
    #setting results --> will change to class system
        return render_template('search.html', results = results, form=form)

    return render_template('search.html',form=form)


class dict_class:
    '''
    TRACK:
    dict_keys(['album', 'artists', 'available_markets', 'disc_number', 'duration_ms', 'explicit', 'external_ids', 
    'external_urls', 'href', 'id', 'is_local', 'name', 'popularity', 'preview_url', 'track_number', 'type', 'uri'])
    '''

    '''
    ARTIST:
    dict_keys(['external_urls', 'followers', 'genres', 'href', 'id', 'images', 'name', 'popularity', 'type', 'uri'])
    '''

    '''
    ALBUM:
    dict_keys(['album_group', 'album_type', 'artists', 'available_markets', 'external_urls', 'href', 'id', 'images',
     'name', 'release_date', 'release_date_precision', 'total_tracks', 'type', 'uri'])
    '''

    '''
    PLAYLIST:
    dict_keys(['collaborative', 'description', 'external_urls', 'href', 'id', 'images', 'name', 'owner', 'primary_color', 
    'public', 'snapshot_id', 'tracks', 'type', 'uri'])
    '''

    '''
    IMAGE:
    dict_keys(['height', 'url', 'width'])
    '''
    def __init__(self, **entries):
        self.__dict__.update(entries)

def current_user_recently_played(account, limit=15, after=None, before=None):
    return account._get("me/player/recently-played", limit=limit, after=after, before=before)


if __name__ == "__main__":
    app.run(threaded=True,port=8080, debug=True)
