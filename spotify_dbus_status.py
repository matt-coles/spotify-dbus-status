#!/usr/bin/python3
from argparse import ArgumentParser
from sys import stdout, argv

import dbus
import json
import pulsectl

session_bus = dbus.SessionBus()

bus_data = ("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
spotify_bus = session_bus.get_object(*bus_data)

interface = dbus.Interface(spotify_bus, "org.freedesktop.DBus.Properties")
metadata = interface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
status   = interface.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")


def main():

    formats = ('json', 'str')
    parser = ArgumentParser()
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--artist', action='store_true')
    parser.add_argument('--song', action='store_true')
    parser.add_argument('--album', action='store_true')
    parser.add_argument('--volume', action='store_true')
    parser.add_argument('--status', action='store_true')
    parser.add_argument('--format', default='str', choices=formats)
    parser.add_argument('--sep', default=' - ')
    parser.add_argument('--template')

    args = parser.parse_args()

    data_flags = ('status', 'artist', 'song', 'album', 'volume')

    opts = dict()

    # Introspect argparse to get data_flags flags
    for action in parser._actions:
        if action.dest in data_flags:
            for option in action.option_strings:
                opts[option] = action.dest

    # Get the order in which flags were passed
    ordered = tuple(filter(None, (opts.get(arg) for arg in argv[1:])))
    data_flags = ordered or data_flags

    # If no data flags are passed default to all
    if args.all or not any(getattr(args, flag) for flag in data_flags):
        for flag in data_flags:
            setattr(args, flag, True)

    if args.template is None:

        # Find out which data values artist/song/album were present
        template_strings = (flag for flag in data_flags if getattr(args, flag))

        # Create a template string "{artist} {song} ..."
        args.template = args.sep.join([
            '{' + flag + '}' for flag in template_strings
        ])

    data = dict()

    if args.status:
        if str(status) == 'Playing':
            data['status'] = "\uf04c"
        else:
            data['status'] = "\uf04b"

    if args.artist:
        data['artist'] = str(next(iter(metadata.get('xesam:artist'))))

    if args.song:
        data['song'] = str(metadata.get('xesam:title'))

    if args.album:
        data['album'] = str(metadata.get('xesam:album'))

    if args.volume:
        pulse = pulsectl.Pulse('spotify-client')
        spotify = pulse.sink_input_list()[0] # all the sinks are basically the same?
        volume = round(spotify.volume.value_flat*100)
        data['volume'] = '{0}%'.format(volume)

    formatters = {
        'json': lambda d: stdout.write(json.dumps(d)),
        'str': lambda d: stdout.write(args.template.format(**data)),
    }

    formatters.get(args.format)(data)


if __name__ == '__main__':
    main()
