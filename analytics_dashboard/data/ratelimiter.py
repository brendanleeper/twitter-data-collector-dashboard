from operator import contains
import os, requests, json
from .auth import create_headers
from .request import request
from django.utils.timezone import now
from datetime import timedelta
from . import ratelimits

class RateLimiter(object):
    def __init__(self, **kwargs):
        self._endpoint_limits = {}
        for endpoint in ratelimits.RATE_LIMITS.keys():
            self._endpoint_limits[endpoint] = Limit(endpoint, ratelimits.RATE_LIMITS[endpoint])

    def check_limits(self, endpoints):
        url = "https://api.twitter.com/1.1/application/rate_limit_status.json"
        if isinstance(endpoints, list):
            endpoints = ','.join(endpoints)
        params = {'resources': endpoints}

        response = requests.request("GET", url, headers = create_headers(), params = params)
        print("Endpoint Response Code: " + str(response.status_code))
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        return response.json()

    def check_request(self, request: request):
        print('checking request: %s' % request)
        (passed, sleep) = self._endpoint_limits[request.endpoint].check()
        if passed:
            print('endpoint %s is under the rate limit' % request.endpoint)
            return True, None
        else:
            return False, sleep

    def endpoint_used(self, endpoint):
        self._endpoint_limits[endpoint].increment()

class Limit(object):
    def __init__(self, endpoint, limit) -> None:
        self.endpoint = endpoint
        self.limit = limit
        self._limit_used = 0
        self.window_start = None
        print('created limit for endpoint %s : %d' % (endpoint, limit))

    def __str__(self) -> str:
        return self.endpoint + ' :: ' + str(self.limit)

    def check(self):
        self._check_window()
        print('checking endpoint %s, currently %s/%s' % (self.endpoint, self._limit_used, self.limit))
        if self._limit_used < self.limit or self.window_start is None:
            return True, 0
        print('endpoint %s maxed out until %s' % (self.endpoint, self.window_start + timedelta(minutes=15)))
        return self._limit_used < self.limit, (self.window_start + timedelta(minutes=15))

    def _free(self):
        self._limit_used = 0
        self.window_start = None

    def _check_window(self):
        if self.window_start is None:
            return
        if (now() - timedelta(minutes=15)) > self.window_start:
            # free the window and reset the limit
            print('reseting window on endpoint %s' % self.endpoint)
            self._free()

    def increment(self):
        if self.window_start is None:
            self.window_start = now()
        self._limit_used = self._limit_used + 1
        print('incrementing limit %s, is now %d/%d' % (self.endpoint, self._limit_used, self.limit))
