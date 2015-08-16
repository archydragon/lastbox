#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Last.fm submission script for Rockbox' scrobbler.log. Nothin special.
# Connect (and mount) your player to the computer, then run this code without
# any additional arguments (bells and whistles will be improved a bit later).


import subprocess
import sys
import os
import os.path
import getpass
import codecs
import time
import json
import urllib
import urllib2
import cPickle
import hashlib


VERSION = "0.2.0"
DATA_DIR = os.path.expanduser("~") + "/.config/lastbox/"
KNOWN_FILE = DATA_DIR + 'known.db'
IGNORE_FILE = DATA_DIR + 'ignore.db'
CACHE_FILE = DATA_DIR + 'cache.db'
API_KEY = '41f9449ba39bf20dea4c163632fbd52c'
API_SEC = 'e6d1ee7832631912c72ece20126469a9'
API_FMT = 'https://ws.audioscrobbler.com/2.0/?method={0}&api_key={1}&format=json'


# RAINBOWS, RAINBOWS!!
class colors:
    BRIGHT = '\033[1m'
    WHITE = '\033[37m'
    MAGENTA = '\033[35m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    ENDC = '\033[0m'


# Read serialized database
def db_get(db):
    try:
        f = open(db, "rb")
    except IOError:
        data = []
    else:
        data = cPickle.load(f)
        f.close()
    return data

# Save to serialized database
def db_save(db, data):
    with open(db, "wb") as f:
        cPickle.dump(data, f)
        f.close()
    return 0


# Convert local timestampts to UTC
def utc_timestamp(ts):
    return str(int(ts) + time.timezone - (time.daylight * 3600))

# Make API query
def api_query(method, params):
    http_data = urllib.urlencode(params)
    http_url = API_FMT.format(method, API_KEY)
    req = urllib2.Request(http_url, http_data)
    try:
        response = urllib2.urlopen(req)
        return response.read()
    except urllib2.URLError as e:
        raise e

# Sign API query
def sign(method, dic):
    out = ""
    dic['method'] = method
    for key in sorted(dic):
        out += key + dic[key]
    h = hashlib.md5()
    h.update(out + API_SEC)
    return h.hexdigest()

# Sign scrobble query and do it
def scrobble_push(params, is_from_cache):
    if not is_from_cache:
        params["api_sig"] = sign('track.scrobble', params)
    try:
        api_query('track.scrobble', params)
        if is_from_cache:
            cache = db_get(CACHE_FILE)
            cache.remove(params)
            db_save(CACHE_FILE, cache)
        return True
    except urllib2.URLError as e:
        print colors.RED + "HTTP error when submitting some tracks: " \
            + colors.BRIGHT + str(e) + colors.ENDC
        if not is_from_cache:
            cache = db_get(CACHE_FILE)
            cache.append(params)
            db_save(CACHE_FILE, cache)
        return False

# Generate scrobble query parameters
def scrobble(queue, token):
    i = 0
    params = {}
    for song in queue:
        ci = i % 10
        if ci == 0 and params != {}:
            if scrobble_push(params, False):
                print "Submitted {0} of {1} tracks".format(i, len(queue))
            params = {}
        params["artist[{0}]".format(ci)]    = song['artist'].encode('utf-8')
        params["track[{0}]".format(ci)]     = song['track'].encode('utf-8')
        params["album[{0}]".format(ci)]     = song['album'].encode('utf-8')
        params["timestamp[{0}]".format(ci)] = utc_timestamp(song['timestamp'])
        params["api_key"]                   = API_KEY
        params["sk"]                        = token
        i += 1
    if params != {}:
        if scrobble_push(params, False):
            print "Submitted {0} of {0} tracks".format(len(queue))
    print colors.GREEN + "Done!\n" + colors.ENDC
    return 0


# Add new user
def add_user():
    authentified = False
    while not authentified:
        username = raw_input(colors.WHITE + "Enter last.fm username: " + colors.ENDC).strip()
        password = getpass.getpass(colors.WHITE + "Enter last.fm password: " + colors.ENDC)
        params = { "username": username,
                   "password": password,
                   "api_key": API_KEY }
        params['api_sig'] = sign('auth.getMobileSession', params)
        try_auth = json.loads(api_query('auth.getMobileSession', params))
        if 'session' in try_auth:
            authentified = True
            token = try_auth['session']['key']
            with open(DATA_DIR + "/default", "w") as f:
                f.write(username)
                f.close()
            with open(DATA_DIR + "/" + username + ".key", "w") as f:
                f.write(token)
                f.close()
        else:
            print colors.RED + "Authentication failed!" + colors.ENDC
            authentified = False
    return (username, token)

# Authenticate
def auth():
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR)
        return add_user()
    else:
        try:
            with open(DATA_DIR + "/default", "r") as f:
                username = f.read().strip()
            with open(DATA_DIR + "/" + username + ".key", "r") as f:
                token = f.read().strip()
            return (username, token)
        except IOError:
            return add_user()

# Read log from player
def get_raw_log():
    # find player devices
    devices = []
    for line in subprocess.check_output(['mount']).split('\n'):
        if (line.find('type vfat') > 0) or (line.find('(msdos') > 0):
            devices.append(line.split(' ', 2)[2].split('(')[0].strip())
    # find log files
    logfiles = []
    for d in devices:
        logfile = d + '/.scrobbler.log'
        if os.path.isfile(logfile):
            logfiles.append(logfile)
    # TODO: ability to choose log file
    try:
        used_log = logfiles[0]
    except IndexError:
        print colors.RED + "There are no players with accessible scrobbled logs!\n" + colors.ENDC
        sys.exit()
    # read log file
    with codecs.open(used_log, "r", "utf-8") as f:
        raw = f.read().split('\n')
    os.remove(used_log)
    return raw


def main():
    print colors.MAGENTA + "Lastbox v" + VERSION + colors.ENDC + "\n"

    (username, token) = auth()
    print "Hello,", colors.WHITE + username + colors.ENDC + "!"

    # try to submit tracks that failed to submit previous time(s)
    cache = db_get(CACHE_FILE)
    if cache:
        print "Found tracks failed to submit previous time(s), trying to push them now..."
        results = []
        for item in cache:
            scrobble_push(item, True)

    raw = get_raw_log()

    # parse log file
    tracks_total = 0
    songs = []
    for song in raw:
        if song.find('\t') > 0:
            s = song.split('\t')
            track = {}
            track['artist'] = s[0]
            track['album']  = s[1]
            track['track']  = s[2]
            track['number'] = s[3]
            track['timestamp'] = s[6]
            tracks_total += 1
            if s[5] == "L":
                songs.append(track)

    print "Found", colors.GREEN + str(tracks_total) + colors.ENDC, "track records in log,", \
        colors.GREEN + str(len(songs)) + colors.ENDC, "of them were not skipped.\n"

    queue = []
    for s in songs:
        knowns = db_get(KNOWN_FILE)
        ignores = db_get(IGNORE_FILE)
        if s['artist'] not in ignores and s['artist'] not in knowns:
            params = { "artist": s['artist'].encode('utf-8'),
                       "username": username }
            data = json.loads(api_query('artist.getInfo', params))
            try:
                plays = data['artist']['stats']['userplaycount']
            except KeyError:
                prompt = "You've never listened " + colors.YELLOW + s['artist'].encode('utf-8') + \
                    colors.ENDC + " before, do you want to scrobble it?" + \
                    " Y - yes, N - no and add it to ignore list: "
                confirm = raw_input(prompt).strip()
                if confirm.lower() == "n":
                    ignores.append(s['artist'])
                    db_save(IGNORE_FILE, ignores)
                else:
                    knowns.append(s['artist'])
                    db_save(KNOWN_FILE, knowns)
            else:
                knowns.append(s['artist'])
                db_save(KNOWN_FILE, knowns)
            time.sleep(1)
        if s['artist'] not in ignores:
            queue.append(s)

    scrobble(queue, token)
    return 0


if __name__ == "__main__":
    main()
