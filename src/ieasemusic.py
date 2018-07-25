
# -*- coding: UTF-8 -*-

import sys
import socket
import json
import pinyin
from workflow import Workflow3

BUFF_SIZE = 4096
SOCKET_FILENAME = '/var/tmp/ieasemusic.sock'


def flush(s):
    try:
        data = b''

        while True:
            chunk = s.recv(BUFF_SIZE)
            data += chunk

            if len(chunk) < BUFF_SIZE:
                break
    except Exception as e:
        raise e

    return data


class Controller:
    def __init__(self, wf):
        global status
        self.wf = wf
        try:
            status = self.__getStatus()
        except Exception:
            wf.add_item(
                title='Player is not runing...',
                subtitle='Please start ieasemusic or update to new version.'
            )
            wf.send_feedback()
            sys.exit(0)

    def __formatArtists(self, artists):
        artists = artists.values() if not isinstance(
            artists, list) else artists

        return '/'.join(
                map(
                    lambda v: v['name'],
                    iter(artists)
                )
        )

    def __isMatched(self, item, keywords):
        matchTitlte = pinyin.get(
            item['name'],
            format='strip',
            delimiter=''
        ).lower().find(keywords) != -1

        matchArtists = pinyin.get(
            self.__formatArtists(item['artists']),
            format='strip',
            delimiter=''
        ).lower().find(keywords) != -1

        return matchTitlte or matchArtists

    def __getStatus(self):
        s = socket.socket(socket.AF_UNIX)

        # 1 second timeout, after all it should be instant because its local
        s.settimeout(1)
        s.connect(SOCKET_FILENAME)

        data = flush(s)
        return json.loads(data)

    def __getQuery(self):
        wf = self.wf
        return (wf.args[0] if len(wf.args) else '').strip()

    def __out(self, res):
        for v in res:
            self.wf.add_item(**v)

        self.wf.send_feedback()

    def getPlaying(self):
        track = status['track']
        playing = status['playing']

        return [
            {
                'title': track['name'],
                'subtitle': self.__formatArtists(track['artists']),
                'valid': True,
                'arg': json.dumps({'command': 'toggle'}),
                'icon': './images/tada.png' if playing == 1 else './images/mask.png' # noqa
            },
            {
                'title': 'Next',
                'subtitle': 'Play the next track.',
                'valid': True,
                'arg': json.dumps({'command': 'next'}),
                'icon': './images/fast_forward.png',
            },
            {
                'title': 'Previous',
                'subtitle': 'Play the previous track.',
                'valid': True,
                'arg': json.dumps({'command': 'prev'}),
                'icon': './images/rewind.png'
            },
            {
                'title': 'Show playlist.',
                'valid': True,
                'arg': '--show-playlist',
                'icon': './images/pig.png'
            },
            {
                'title': 'Change mode.',
                'valid': True,
                'arg': '--change-mode',
                'icon': './images/koala.png'
            },
            {
                'title': 'Toggle the mian window.',
                'valid': True,
                'arg': json.dumps({'command': 'show'}),
                'icon': './images/bear.png'
            },
            {
                'title': 'Quit.',
                'valid': True,
                'arg': json.dumps({'command': 'goodbye'}),
                'icon': './images/dog.png'
            },
            {
                'title': 'Bug report 🐛',
                'valid': True,
                'arg': json.dumps({'command': 'bug'}),
                'icon': './images/cat.png'
            },
        ]

    def getPlaylist(self, query):
        playlist = status['playlist']
        filtered = [
            i for i in playlist
            if self.__isMatched(i, query)
        ]

        return map(
            lambda v: (
                {
                    'title': v['name'],
                    'subtitle': self.__formatArtists(v['artists']),
                    'arg': json.dumps({'command': 'play', 'id': v['id']}),
                    'valid': True,
                    'icon': './images/lollipop.png'
                }
            ),
            filtered
        )

    def showPlaylist(self):
        query = self.__getQuery()
        res = self.getPlaylist(query)
        self.__out(res)

    def showMenu(self):
        query = self.__getQuery()
        res = self.getPlaying()

        if query:
            res = [
                i for i in res
                if pinyin.get(
                    i['title'],
                    format='strip',
                    delimiter=''
                ).lower().find(query) != -1
            ]

        self.__out(res)

    def showModes(self):
        modes = status['modes']
        names = ('Shuffle.', 'Repeat.', 'Repeat One.')
        icons = ('./images/twisted_rightwards_arrows.png', './images/repeat_one.png', './images/repeat.png') # noqa

        res = map(
            lambda v: (
                {
                    'title': names[v['mode']],
                    'subtitle': 'Enabled' if v['enabled'] == 1 else 'Disabled',
                    'icon': icons[v['mode']],
                    'arg': json.dumps({'command': 'changeMode', 'mode': v['mode']}), # noqa
                    'valid': True
                }
            ),
            modes
        )
        self.__out(res)

    @staticmethod
    def exe(argv):
        try:
            s = socket.socket(socket.AF_UNIX)

            s.settimeout(1)
            s.connect(SOCKET_FILENAME)

            flush(s)
            s.sendall(argv)
        except Exception as e:
            print e
        finally:
            s.close()


if __name__ == '__main__':
    Controller(Workflow3()).showMenu()
