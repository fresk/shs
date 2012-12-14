from kivy.clock import Clock
import json
import urllib2
from os.path import join, exists
from functools import partial
from kivy.network.urlrequest import UrlRequest
from kivy.app import App


class JsonData(object):

    def __init__(self, fname, on_success, on_progress):
        '''Load a json, and return the result in the `on_success` callback.

        :Parameters:
            `on_success`: result
                Return the result of the json load.
            `on_progress`: message, size, total
                Called everytime a file is downloaded.
        '''

        super(JsonData, self).__init__()

        self.cb_success = on_success
        self.cb_progress = on_progress
        self.fname = fname

        # (internal) mode used when json is decoded
        self._json_mode = 'detect' # detect or replace
        # (internal) map one url to one local filename
        self._json_cache = {}
        # (internal) list of all url detected in the json
        self._json_urls = []
        # (internal) current http request
        self._json_req = None
        # (internal) url count to load
        self._json_count = 0

        # first step, list all the resources we need to check
        self._json_mode = 'detect'
        with open(fname, 'r') as fd:
            json.load(fd, object_hook=self._decode_dict)

        print 'Detected {0} urls'.format(len(self._json_urls))
        self._json_count = len(self._json_urls)
        Clock.schedule_interval(self._download_resources, 0)

    def _replace_resources(self):
        # second step, called when all the download are done
        self._json_mode = 'replace'
        with open(self.fname, 'r') as fd:
            result = json.load(fd, object_hook=self._decode_dict)
        self.cb_success(result)

    def _get_local_from_etag(self, etag, ext, suffix=''):
        return join(App.get_running_app().get_data_dir(),
                'resources', '{0}{1}.{2}'.format(etag, suffix, ext))

    def _download_image(self, data):
        if not data['large']:
            return {}
        # check the etag
        etag = data['etag']
        ext = data['large'][0].rsplit('.', 1)[-1]

        if self._json_mode == 'detect':
            #fn = self._get_local_from_etag(etag, ext)
            #print 'fn', fn, exists(fn)
            #if not exists(fn):
                #print 'append full', data['full']
            #    self._json_urls.append((data['full'], etag, ''))
            #else:
            #    self._json_cache[data['full'][0]] = fn
            if data['medium']:
                fn = self._get_local_from_etag(etag, ext, '_medium')
                if not exists(fn):
                    #print 'append medium', data['medium']
                    self._json_urls.append((data['medium'], etag, '_medium'))
                else:
                    #print "adding to cache", data['medium']
                    self._json_cache[data['medium'][0]] = fn
            if data['large']:
                fn = self._get_local_from_etag(etag, ext, '_large')
                if not exists(fn):
                    #print 'append large', data['large']
                    self._json_urls.append((data['large'], etag, '_large'))
                else:
                    self._json_cache[data['large'][0]] = fn
            return data

        if self._json_mode == 'replace':
            #if data['full'][0].startswith('http://'):
            #    data['full'] = self._json_cache.get(data['full'][0])
            if data['medium'] and data['medium'][0].startswith('http://'):
                data['medium'] = self._json_cache.get(data['medium'][0])
            if data['large'] and data['large'][0].startswith('http://'):
                data['large'] = self._json_cache.get(data['large'][0])
            return data

    def _download_resources(self, *args):
        # we finished to download all the resources. now replace.
        if self._json_req is None and not self._json_urls:
            self._replace_resources()
            return False

        # we are still downloading one resource
        if self._json_req is not None:
            return

        # start a resource download
        url_data, etag, suffix = self._json_urls.pop()
        url = url_data[0]
        url = urllib2.quote(url, safe=':/')
        #print "fetching:", url
        self.cb_progress('Downloading resources {0}/{1}'.format(
            self._json_count - len(self._json_urls), self._json_count),
            self._json_count - 1 - len(self._json_urls),
            self._json_count)
        self._json_req = UrlRequest(url,
                on_success=partial(self._on_dget_success, etag, suffix),
                on_progress=self._on_dget_progress,
                on_error=self._on_dget_error)

    def _on_dget_success(self, etag, suffix, req, result, *args):
        url = urllib2.unquote(req.url)
        ext = url.rsplit('.', 1)[-1]
        local_fn = self._get_local_from_etag(etag, ext, suffix)
        self._json_cache[url] = local_fn
        if req.resp_status > 399:
            raise Exception('HTTP GET ERROR: {0} ({1})'.format(
                req.url, req.resp_status))
        with open(local_fn, 'wb') as fd:
            fd.write(result)

        # release the req, the next download will happen in the clock.
        self._json_req = None

    def _on_dget_error(self, *args):
        print 'HTTP GET ERROR?', args
        self._json_req = None

    def _on_dget_progress(self, req, cursize, total):
        step = (cursize / float(total)) if total > 0 else 0
        self.cb_progress('Downloading resources {0}/{1}'.format(
            self._json_count - len(self._json_urls), self._json_count),
            self._json_count - 1 - len(self._json_urls) + step,
            self._json_count)

    def _download_resource(self, url):
        if self._json_mode == 'detect':
            if url not in self._json_urls:
                self._json_urls.append(url)
            return url
        if self._json_mode == 'replace':
            # XXX use a missing image if not found
            return self._json_cache.get(url)


    def _decode_list(self, data):
        rv = []
        for item in data:
            if isinstance(item, unicode):
                item = item.encode('utf-8')
            elif isinstance(item, list):
                item = self._decode_list(item)
            elif isinstance(item, dict):
                item = self._decode_dict(item)
            rv.append(item)
        return rv


    def _decode_dict(self, data):
        rv = {}

        # hook to check if the dict is an image dict
        if 'large' in data and 'etag' in data:
            self._download_image(data)

        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            elif isinstance(value, list):
                value = self._decode_list(value)
            elif isinstance(value, dict):
                value = self._decode_dict(value)
            rv[key] = value
        return rv


'''
# original code
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
'''
