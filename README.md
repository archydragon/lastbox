Lastbox
=======

Last.fm submission script for Rockbox' scrobbler.log. Nothing special.
 
Doesn't require any additional libraries except Python 2.7 installation.

Installation
------------

`pip install lastbox`

or

```
git clone https://github.com/Mendor/lastbox
cd lastbox
python setup.py install
```

Usage
-----
 
1. Connect (and mount) your player to the computer.
2. Run `lastbox` command.
3. If it is run for the first time, it will ask you for username and password (the password isn't kept anywhere so no need to worry).
4. If there are artists you've never listened before, Lastbox will ask if you really want to submit their tracks (I hope, one day Rockbox scrobbler will support 'Album artist` tags).
5. That's all.

License
-------

MIT
