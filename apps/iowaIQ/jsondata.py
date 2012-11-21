from kivy.clock import Clock
import json
import urllib2
from os.path import join, exists
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

    def _download_resources(self, *args):
        # we finished to download all the resources. now replace.
        if self._json_req is None and not self._json_urls:
            self._replace_resources()
            return False

        # we are still downloading one resource
        if self._json_req is not None:
            return

        # start a resource download
        url = urllib2.quote(self._json_urls.pop(), safe=':/')
        self.cb_progress('Downloading resources {0}/{1}'.format(
            self._json_count - len(self._json_urls), self._json_count),
            self._json_count - 1 - len(self._json_urls),
            self._json_count)
        self._json_req = UrlRequest(url,
                on_success=self._on_dhead_success,
                on_error=self._on_dhead_error,
                method='HEAD')

    def _on_dhead_success(self, req, *args):
        if req.resp_status > 399:
            raise Exception('HTTP HEAD ERROR: {0} ({1})'.format(
                req.url, req.resp_status))

        url = urllib2.unquote(req.url)
        etag = req.resp_headers['etag'][1:-1]
        ext = req.resp_headers['content-type'].split('/')[-1]

        # link the url to a local filename
        local_fn = join(App.get_running_app().get_data_dir(),
                'resources', '{0}.{1}'.format(etag, ext))
        self._json_cache[url] = local_fn

        # if the local file is not found, get it.
        if not exists(local_fn):
            self._json_req = UrlRequest(urllib2.quote(url, safe=':/'),
                    on_success=self._on_dget_success,
                    on_progress=self._on_dget_progress,
                    on_error=self._on_dget_error)
            return

        # otherwise, just release the req, the next download will happen in the
        # clock.
        self._json_req = None

    def _on_dhead_error(self, *args):
        self._json_req = None

    def _on_dget_success(self, req, result, *args):
        url = urllib2.unquote(req.url)
        local_fn = self._json_cache[url]
        if req.resp_status > 399:
            raise Exception('HTTP GET ERROR: {0} ({1})'.format(
                req.url, req.resp_status))
        with open(local_fn, 'wb') as fd:
            fd.write(result)

        # release the req, the next download will happen in the clock.
        self._json_req = None

    def _on_dget_error(self, *args):
        # TODO
        pass

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
                if item.startswith("http://"):
                    item = self._download_resource(item)
            elif isinstance(item, list):
                item = self._decode_list(item)
            elif isinstance(item, dict):
                item = self._decode_dict(item)
            rv.append(item)
        return rv


    def _decode_dict(self, data):
        rv = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8')
                if value.startswith("http://"):
                    value = self._download_resource(value)
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
