#! /usr/bin/env python
#
# Mixpanel, Inc. -- http://mixpanel.com/
#
# Python API client library to consume mixpanel.com analytics data.

import os, sys
import pygal
import hashlib
import urllib
import time
try:
    import json
except ImportError:
    import simplejson as json

class Mixpanel(object):

    ENDPOINT = 'http://mixpanel.com/api'
    VERSION = '2.0'

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def request(self, methods, params, format='json'):
        """
            methods - List of methods to be joined, e.g. ['events', 'properties', 'values']
                      will give us http://mixpanel.com/api/2.0/events/properties/values/
            params - Extra parameters associated with method
        """
        params['api_key'] = self.api_key
        params['expire'] = int(time.time()) + 600   # Grant this request 10 minutes.
        params['format'] = format
        if 'sig' in params: del params['sig']
        params['sig'] = self.hash_args(params)

        request_url = '/'.join([self.ENDPOINT, str(self.VERSION)] + methods) + '/?' + self.unicode_urlencode(params)

        request = urllib.urlopen(request_url)
        data = request.read()

        return json.loads(data)

    def unicode_urlencode(self, params):
        """
            Convert lists to JSON encoded strings, and correctly handle any
            unicode URL parameters.
        """
        if isinstance(params, dict):
            params = params.items()
        for i, param in enumerate(params):
            if isinstance(param[1], list):
                params[i] = (param[0], json.dumps(param[1]),)

        return urllib.urlencode(
            [(k, isinstance(v, unicode) and v.encode('utf-8') or v) for k, v in params]
        )

    def hash_args(self, args, secret=None):
        """
            Hashes arguments by joining key=value pairs, appending a secret, and
            then taking the MD5 hex digest.
        """
        for a in args:
            if isinstance(args[a], list): args[a] = json.dumps(args[a])

        args_joined = ''
        for a in sorted(args.keys()):
            if isinstance(a, unicode):
                args_joined += a.encode('utf-8')
            else:
                args_joined += str(a)

            args_joined += '='

            if isinstance(args[a], unicode):
                args_joined += args[a].encode('utf-8')
            else:
                args_joined += str(args[a])

        hash = hashlib.md5(args_joined)

        if secret:
            hash.update(secret)
        elif self.api_secret:
            hash.update(self.api_secret)
        return hash.hexdigest()

def check_for_api_error(data):
    if 'error' in data:
        sys.exit('Error: ' + data['error'])

if __name__ == '__main__':
    api = Mixpanel(
        api_key = os.environ.get('MP_API_KEY'),
        api_secret = os.environ.get('MP_API_SECRET')
    )
    SVG_DIR = 'charts/'
    if not os.path.exists(SVG_DIR):
        os.makedirs(SVG_DIR)
    eventNames = api.request(['events', 'names'], {
        'type': 'general'
    })
    check_for_api_error(eventNames)
    # print json.dumps(eventNames, indent=4)
    data = api.request(['events'], {
        'event' : eventNames,
        'unit' : 'day',
        'interval' : 31,
        'type': 'general'
    })
    check_for_api_error(data)
    # print json.dumps(data, indent=4, sort_keys=True)
    events_chart = pygal.Line(title=u'Events', x_label_rotation=50, human_readable=True)
    events_chart.x_labels = [''] + sorted(data['data']['series'])
    for event in eventNames:
        data_points = []
        for key in sorted(data['data']['values'][event].keys()):
            data_points.append(data['data']['values'][event][key])
        events_chart.add(event, data_points)
    events_chart.render_to_file(SVG_DIR + 'Events.svg')

    relevant_properties = {'About': ('Team',), 'Scrolled to': ('Home', 'About'), 'Nav Bar': ('Name',), 'DS': ('Carousel', 'Event Brite', 'Past Events'), 'Join Us': ('Header', 'Footer', 'Position Name'), 'Careers': ('Link Click', 'Position Name'), 'Home': ('BePartOfTheMoment', 'Carousel', 'Newsletter', 'WeChallangeThatsPossible'), 'Contact': ('Campus Ambassador', 'General Inquiry'), 'NTV': ('Video Name',), 'Footer': ('Link', 'Link Name')}
    for event, properties in relevant_properties.iteritems():
        for propertyName in properties:
            data = api.request(['events', 'properties'], {
                'event' : event,
                'name': propertyName,
                'unit' : 'day',
                'interval' : 31,
                'type': 'general'
            })
            check_for_api_error(data)
            # print json.dumps(data, indent=4, sort_keys=True)
            events_chart = pygal.StackedBar(title=event + ': ' + propertyName, x_label_rotation=50, human_readable=True)
            events_chart.x_labels = [''] + sorted(data['data']['series'])
            for propertyValue in sorted(data['data']['values'].keys()):
                if propertyValue != 'undefined':
                    data_points = []
                    for key in sorted(data['data']['values'][propertyValue].keys()):
                        data_points.append(data['data']['values'][propertyValue][key])
                    events_chart.add(propertyValue, data_points)
            events_chart.render_to_file(SVG_DIR + event + '_' + propertyName + '.svg')
