import json
import urllib2
import requests
import os
from os.path import join, exists

API_URL = 'http://www.fresksite.net/dcadb/wp-content/themes/dca/api/%s.php'

import HTMLParser
_htmlparser = HTMLParser.HTMLParser()
unescape = _htmlparser.unescape


class JsonDataLoader(object):

    def __init__(self, dataset, storage_dir='resources'):
        self._downloads = []
        self.dataset = dataset
        self.storage_dir = storage_dir
        self.fname = "%s.json" % self.dataset
        self.raw_fname = join(self.storage_dir, "_"+self.fname)

        self.fetch_raw_dataset()
        self.parse_dataset()
        self.download_resources()

    def save(self, fname):
        with open(fname, 'w') as fout:
            json.dump(self.data, fout)

    def download_resources(self):
        for d in self._downloads:
            print "downloading", d['etag']
            if not d['etag']:
                continue
            cache_name = self.cache_name(d)
            if exists(cache_name):
                continue
            r = requests.get(d['full'][0])
            with open(cache_name, 'wb') as fout:
                fout.write(r.content)

    def cache_name(self, data):
        etag = data['etag']
        ext = data['full'][0].rsplit('.', 1)[-1]
        return self._local_name_from_etag(etag, ext)

    def fetch_raw_dataset(self):
        r = requests.get(API_URL % self.dataset)
        json.dump(r.json, open(self.raw_fname, 'w'))

    def parse_dataset(self):
        self.data = json.load(open(self.raw_fname, 'r'), object_hook=self._decode_dict)

    def _local_name_from_etag(self, etag, ext, suffix=''):
        return join(self.storage_dir, '{0}{1}.{2}'.format(etag, suffix, ext))

    def _decode_list(self, data):
        rv = []
        for item in data:
            if isinstance(item, unicode):
                item = item.encode('utf-8', 'replace')
            elif isinstance(item, list):
                item = self._decode_list(item)
            elif isinstance(item, dict):
                item = self._decode_dict(item)
            rv.append(item)
        return rv

    def _decode_dict(self, data):
        rv = {}

        # hook to check if the dict is an image dict
        if 'full' in data and 'etag' in data:
            if data['full']:
                self._downloads.append(data)
                return self.cache_name(data)
            else:
                return None

        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = unescape(key.encode('utf-8', 'replace'))
            if isinstance(value, unicode):
                value = unescape(value.encode('utf-8', 'replace'))
            elif isinstance(value, list):
                value = self._decode_list(value)
            elif isinstance(value, dict):
                value = self._decode_dict(value)
            rv[key] = value
        return rv


if not exists('./resources'):
    os.mkdir("resources")

print "updating history scrachtes..."
scratches = JsonDataLoader("scratches")
scratches.save('resources/scratches.json')

print "updating historic sites..."
scratches = JsonDataLoader("historicsites")
scratches.save('resources/historicsites.json')

print "updating iowans in hollywood..."
scratches = JsonDataLoader("hollywood")
scratches.save('resources/hollywood.json')

print "updating medal of honor iowans..."
scratches = JsonDataLoader("medals")
scratches.save('resources/medals.json')



print "updating county wiki..."
countywiki = JsonDataLoader("countywiki")
countywiki.save('resources/countywiki.json')




