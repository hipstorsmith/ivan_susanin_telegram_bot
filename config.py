import os
from urllib.parse import urlparse

TG_TOKEN = os.getenv('TG_TOKEN')
GMAPS_TOKEN = os.getenv('GMAPS_TOKEN')

DEFAULT_USER_DATA = {'mode': 'driving',
                     'origin': None,
                     'destination': None,
                     'waypoints': [],
                     'units': 'metric',
                     'avoid': {'tolls': False,
                               'highways': False,
                               'ferries': False,
                               'indoor': False},
                     'departure_time': 'now',
                     'traffic_model': 'best_guess',
                     'transit_mode': {'bus': False,
                                      'subway': False,
                                      'train': False,
                                      'tram': False,
                                      'rail': False},
                     'transit_routing_preference': '',
                     'step': 0,
                     'directions': None
                     }

DEFAULT_GEO_DATA = {'origin': None,
                    'destination': None,
                    'waypoints': [],
                    'step': 0,
                    'directions': None
                    }

redis_url = os.getenv('REDIS_URL', '127.0.0.1:6379')
redis_host, redis_port = redis_url.rsplit(':', 1)
try:
    redis_password, redis_host = redis_host.rsplit('@', 1)
    redis_user, redis_password = redis_password.rsplit(':', 1)
except ValueError:
    redis_user, redis_password = '', ''

GMAPS_DIRECTIONS_URL = 'https://maps.googleapis.com/maps/api/directions/json?'
GMAPS_IMAGE_URL = 'https://maps.googleapis.com/maps/api/streetview?'
