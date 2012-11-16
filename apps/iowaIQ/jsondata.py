import os
import json
import urllib2
import httplib2


def load(fname):
    return json.load(open(fname, 'r'), object_hook=_decode_dict)

def _download_resource(url):
    h = httplib2.Http()
    url = urllib2.quote(url, safe=':/')
    resp, content = h.request(url, "HEAD")
    if resp['status'] > '399':
        raise Exception("HTTP ERROR: %s"%resp)

    ext = resp['content-type'].split('/')[-1]
    cache_name = "resources/{0}.{1}".format(resp['etag'][1:-1], ext)
    if os.path.exists(cache_name):
        return cache_name

    resp, content = h.request(url, "GET")
    if resp['status'] > '399':
        raise Exception("HTTP ERROR: %s"%resp)
    fout = open(cache_name, 'w').write(content)
    return cache_name


def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
            if item.startswith("http://"):
                item = _download_resource(item)
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv


def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
            if value.startswith("http://"):
                value = _download_resource(value)
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv

