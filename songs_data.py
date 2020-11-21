import json
import os


class Singleton(object):
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance


class SongsDataManager(Singleton):
    def __init__(self):
        self._data = {}
        if not os.path.exists('songs_data.json'):
            with open('songs_data.json', 'w') as fp:
                fp.write('{}')

    def read_songs_data(self):
        with open('songs_data.json', 'r') as fp:
            self._data = json.load(fp)
        return self._data

    def write_songs_data(self, new_data=None):
        if new_data:
            self._data = new_data
        with open('songs_data.json', 'w') as fp:
            json.dump(self._data, fp)
