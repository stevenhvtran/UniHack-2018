import os
import requests
import random
import base64
from geopy.distance import lonlat, distance
from flask import Blueprint, request, jsonify, make_response
from symphony_app.db import db, User, Gig
from sqlalchemy import true


bp = Blueprint(name='symphony', import_name=__name__, url_prefix='/api')
client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
redirect_uri = 'https://symphony-v2.firebaseapp.com/callback'


def get_access_token(auth_url, callback_type):
    """
    Gets a user's Spotify access token from the callback url and callback type
    :param auth_url: The URL that the user is redirected to once they login
    :param callback_type: Either 'create' or 'join' depending on what the user is doing
    :return: Access token of the user logging in
    """
    access_code = auth_url.split('?code=')[1]
    data = {
        'grant_type': 'authorization_code',
        'code': access_code,
        'redirect_uri': redirect_uri + callback_type,
        'client_id': client_id,
        'client_secret': client_secret
    }
    response = requests.post('https://accounts.spotify.com/api/token', data=data).json()
    return response['access_token']


def get_user_id(access_token):
    """
    Gets the Spotify user id tied to an access token
    :param access_token: The Spotify access token of the user
    :return: The user's Spotify user id
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://api.spotify.com/v1/me', headers=headers).json()
    return response['id']


def get_user_top_tracks(access_token):
    """
    Gets a comma separated list of a user's top 15 tracks
    :param access_token: The user's access token
    :return: Comma separated list of track ids
    """
    response = requests.get('https://api.spotify.com/v1/me/top/tracks',
                            params={'limit': 15},
                            headers={'Authorization': f'Bearer {access_token}'}).json()
    track_ids = [track['id'] for track in response['items']]
    track_ids = ','.join(track_ids)
    return track_ids


def create_playlist(host_token, user_id, gig_name):
    """
    Creates a playlist in the user's account with the same name as the gig
    :param host_token: The host's access token
    :param user_id: The host's user id
    :param gig_name: The name of the gig
    :return: The id of the playlist, the URL of the playlist and the playlist URI
    """
    headers = {'Authorization': f'Bearer {host_token}',
               'Content-Type': 'application/json'}
    params = {'name': gig_name}
    response = requests.post(f'https://api.spotify.com/v1/users/{user_id}/playlists',
                             headers=headers,
                             json=params).json()
    return response['id'], response['href'], response['uri']


def upload_playlist_cover_image(host_token, user_id, playlist_id):
    """
    Uploads a random playlist image cover to a created playlist
    :param host_token: The access token of the host of the playlist
    :param user_id: The user id of the host
    :param playlist_id: The playlist id of the created playlist
    :return: None
    """
    image_number = random.randint(0, 5)  # Randomises the playlist cover image number
    with open(f'./symphony_app/playlist_images/playlist_image{image_number}.jpeg', 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read())

    headers = {'Authorization': f'Bearer {host_token}',
               'Content-Type': 'image/jpeg'}
    requests.put(f'https://api.spotify.com/v1/users/{user_id}/playlists/{playlist_id}/images',
                 headers=headers,
                 data=encoded_image)


def get_recommendations(access_token, seed_tracks, no_users, settings_list):
    """
    Gets recommended tracks based on a list of seed tracks
    :param access_token: The host's access token
    :param seed_tracks: A comma separated list of tracks
    :param no_users: The number of users to generate recommendations for
    :param settings_list: A list of strings, either  0,1 or 2. Allows for finetuning with recommendation algorithm
    :return: Returns a list of track uris
    """
    settings_list = map(int, settings_list)
    settings_targets = [0, None, 1]
    option_names = ['danceability', 'energy', 'instrumentalness', 'valence']

    settings_dict = {}
    if settings_list:
        for option_num, option in enumerate(settings_list):
            target = settings_targets[option]
            if target:
                option_name = f'target_{option_names[option_num]}'
                settings_dict.update({option_name: target})

    playlist_tracks = []
    seed_tracks = seed_tracks.split(',')
    for seeding in range(no_users):
        seed_list = random.sample(seed_tracks, 5)
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'limit': 10, 'seed_tracks': ','.join(seed_list)}
        params.update(settings_dict)
        response = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params).json()
        playlist_tracks += [track['uri'] for track in response['tracks']]
    return playlist_tracks


def add_tracks_to_playlist(host_token, host_id, playlist_id, playlist_tracks):
    """
    Adds list of track uris to a playlist
    :param host_token: The access token of the host of the gig
    :param host_id: The user id of the host
    :param playlist_id: The playlist id of the gig
    :param playlist_tracks: The list of track uris to be added to the playlist
    :return: None
    """
    url = f'https://api.spotify.com/v1/users/{host_id}/playlists/{playlist_id}/tracks'
    headers = {'Authorization': f'Bearer {host_token}',
               'Content-Type': 'application/json'}
    while playlist_tracks:
        tracks_list = playlist_tracks[0:90]
        requests.post(url, headers=headers, json={'uris': tracks_list})
        del playlist_tracks[0:90]


@bp.route('/create', methods=('POST',))
def create_gig():
    response = request.get_json()
    longitude, latitude = float(response['longitude']), float(response['latitude'])
    gig_name = str(response['gig_name'])
    auth_url = response['url']

    access_token = get_access_token(auth_url, 'create')
    spotify_id = get_user_id(access_token)
    users_top_tracks = get_user_top_tracks(access_token)
    playlist_id, playlist_url, playlist_uri = create_playlist(access_token, spotify_id, gig_name)
    upload_playlist_cover_image(access_token, spotify_id, playlist_id)

    settings_list = []
    if 'settings' in response:
        settings_list = map(str, response['settings'])  # Convert settings list to contain strings

    recommendations = get_recommendations(access_token, users_top_tracks, 1, settings_list)
    add_tracks_to_playlist(access_token, spotify_id, playlist_id, recommendations)

    gig = Gig(
        gig_name=gig_name,
        playlist_id=playlist_id,
        playlist_url=playlist_url,
        playlist_uri=playlist_uri,
        settings=' '.join(settings_list)
    )
    db.session.add(gig)
    db.session.commit()
    user = User(
        access_token=access_token,
        spotify_id=spotify_id,
        is_host=True,
        gig_id=gig.id,
        top_tracks=users_top_tracks,
        longitude=longitude,
        latitude=latitude,
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Gig created successfully', 'id': spotify_id, 'uri': playlist_uri})


def clear_tracks_in_playlist(host_id, host_token, playlist_id):
    """
    Clears all of the tracks in a playlist
    :param host_id: The user id of the host of the gig
    :param host_token: The access token of the host
    :param playlist_id: The id of the gig's playlist
    :return: None
    """
    url = f'https://api.spotify.com/v1/users/{host_id}/playlists/{playlist_id}/tracks'
    headers = {'Authorization': f'Bearer {host_token}',
               'Content-Type': 'application/json'}
    requests.put(url, headers=headers, json={'uris': []})


def get_gig_details(gig_id):
    """
    Gets various information from a gig
    :param gig_id: The id of the gig
    :return: Comma separated top tracks, amount of users in gig, playlist id, playlist settings, playlist uri
    """
    gig = Gig.query.filter(Gig.id == gig_id).first()
    top_tracks = [user.top_tracks for user in gig.users]
    top_tracks = ','.join(top_tracks)
    return top_tracks, len(gig.users), gig.playlist_id, gig.settings.split(), gig.playlist_uri


@bp.route('/join', methods=('POST',))
def get_gigs():
    response = request.get_json()
    latitude, longitude = response['latitude'], response['longitude']
    user_location = lonlat(longitude, latitude)
    auth_url = response['url']

    access_token = get_access_token(auth_url, 'join')
    spotify_id = get_user_id(access_token)
    users_top_tracks = get_user_top_tracks(access_token)

    user = User(
        access_token=access_token,
        spotify_id=spotify_id,
        is_host=False,
        top_tracks=users_top_tracks,
        longitude=longitude,
        latitude=latitude,
    )

    db.session.add(user)
    db.session.commit()

    # Check if any gigs are in range
    host_users = list(User.query.filter(User.is_host == true()).all())
    gigs_in_range = []
    for host in host_users:
        host_location = lonlat(host.longitude, host.latitude)
        if distance(host_location, user_location).meters < 1000:
            gig_name = Gig.query.filter(Gig.id == host.gig_id).first().gig_name
            gigs_in_range.append({'gig_name': gig_name, 'id': host.gig_id})

    if not gigs_in_range:
        return make_response(jsonify({'error': 'Not in location of a gig'}), 400)
    return jsonify({'message': 'Playlist Updated', 'id': spotify_id, 'gigs': gigs_in_range})


def update_playlist(host, gig_id):
    """
    Updates a playlist with re-seeded recommendations
    :param host: The db User object for the host
    :param gig_id: The id of the gig to re-seed
    :return: The updated playlist URI
    """
    top_tracks, no_users, playlist_id, settings_list, playlist_uri = get_gig_details(gig_id)
    recommendations = get_recommendations(host.access_token, top_tracks, no_users, settings_list)
    clear_tracks_in_playlist(host.spotify_id, host.access_token, playlist_id)
    add_tracks_to_playlist(host.access_token, host.spotify_id, playlist_id, recommendations)
    return playlist_uri


@bp.route('/join/<int:gig_id>', methods=('POST', ))
def join_a_gig(gig_id):
    response = request.get_json()
    spotify_id = response['id']

    # Adds the user to a gig
    user = User.query.filter(User.spotify_id == spotify_id).first()
    user.gig_id = gig_id
    db.session.commit()

    host = User.query.filter(User.is_host == true(), User.gig_id == gig_id).first()
    playlist_uri = update_playlist(host, gig_id)

    return jsonify({'message': 'Playlist joined', 'url': playlist_uri})


@bp.route('/leave', methods=('DELETE',))
def leave_gig():
    response = request.get_json()
    user_id = response['id']

    # Removes user from the gig
    user = User.query.filter(User.spotify_id == user_id).first()
    gig_id = user.gig_id

    if user.is_host:
        gig = Gig.query.filter(Gig.id == gig_id).first()
        users_in_gig = User.query.filter(User.gig_id == gig_id).all()
        [db.session.delete(user) for user in users_in_gig]
        db.session.delete(gig)
        db.session.commit()
    else:
        db.session.delete(user)
        db.session.commit()
        host = User.query.filter(User.gig_id == gig_id, User.is_host == true())
        update_playlist(host,  gig_id)

    return jsonify({'message': 'User left successfully'})
