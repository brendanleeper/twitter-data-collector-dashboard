import os, json
import sqlite3
from django.utils.timezone import now
from dateutil import parser
from threading import Thread
from time import sleep
from datetime import timedelta
from .ratelimiter import RateLimiter
from .request import request

def liking_users(tweetid):
    url = "https://api.twitter.com/2/tweets/{}/liking_users".format(tweetid)
    query_params = {'pagination_token': {}}
    endpoint = '/tweets/:id/liking_users'
    return (url, query_params, endpoint)

def retweets(tweetid):
    url = "https://api.twitter.com/2/tweets/{}/retweeted_by".format(tweetid)
    query_params = {'pagination_token': {}}
    endpoint = '/tweets/:id/retweeted_by'
    return (url, query_params, endpoint)

def tweet_info(tweetid):
    url = "https://api.twitter.com/2/tweets/{}".format(tweetid)
    query_params = {'expansions': 'author_id,attachments.media_keys', 'user.fields': 'id,name,username', 'tweet.fields': 'created_at,public_metrics', 'media.fields': 'public_metrics,preview_image_url,url,variants'}
    endpoint = '/tweets/:id'
    return (url, query_params, endpoint)

def liked_tweets(userid):
    url = "https://api.twitter.com/2/users/{}/liked_tweets".format(userid)
    query_params = {'expansions': 'author_id', 'user.fields': 'description,id,name,username,url', 'pagination_token': {}}
    endpoint = '/users/:id/liked_tweets'
    return (url, query_params, endpoint)

def followers(userid):
    url = "https://api.twitter.com/2/users/{}/followers".format(userid)
    query_params = {'pagination_token': {}}
    endpoint = '/users/:id/followers'
    return (url, query_params, endpoint)

def following(userid):
    url = "https://api.twitter.com/2/users/{}/following".format(userid)
    query_params = {'pagination_token': {}}
    endpoint = '/users/:id/following'
    return (url, query_params, endpoint)

def user_lookup(userid):
    url = "https://api.twitter.com/2/users/{}".format(userid)
    query_params = {'user.fields': 'id,name,username,created_at,description,public_metrics,verified'}
    endpoint = '/users/:id'
    return (url, query_params, endpoint)

def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None

# limiter which manages all requests
# queue of requests to fill
# every 15 mins, checks the queue

class Collector(Thread):
    def __init__(self):
        self._functions = {
            'liking_users': liking_users,
            'retweets': retweets,
            'tweet_info': tweet_info,
            'liked_tweets': liked_tweets,
            'followers': followers,
            'following': following,
            'user_lookup': user_lookup
        }
        Thread.__init__(self)
        self.daemon = True
        self.ratelimiter = RateLimiter()

    # override Thread.run()
    def run(self):
        from .models import ApiTasks
        from django.db.models import Q
        self._is_running = True
        print('Collector starting')
        sleep(3)

        while self._is_running:
            print('collector loop')
            wake_time = now()
            tasks = ApiTasks.objects.filter(Q(hold_until__isnull=True) | Q(hold_until__lt=now())).order_by('created')
            for t in tasks:
                req = request(*self._functions[t.task](t.task_id))
                print(req)
                print(t.created)
                passed, hold = self.ratelimiter.check_request(req)
                if passed:
                    parse_tweet(req.connect_to_endpoint())
                    self.ratelimiter.endpoint_used(req.endpoint)
                    t.delete()
                else:
                    ApiTasks.objects.filter(pk=t.pk).update(hold_until=hold)
                    print('holding on: %s' % req)
                sleep(1)
            snooze = ((wake_time + timedelta(seconds=60-(now() - wake_time).total_seconds()))-wake_time).total_seconds()
            print('sleeping for: {}'.format(snooze))
            sleep(snooze)

    def stop(self):
        self._is_running = False
        print('Collector stopping')


def parse_tweet(response):
    from .models import Tweet, User, Media, TweetMetrics
    print('parsing tweet')

    t = get_or_none(Tweet, id=response['data']['id'])

    if t is None:
        # new tweet
        author = get_or_none(User, id=response['data']['author_id'])
        if author is None:
            author = User.objects.create(
                id=response['data']['author_id'], 
                username=response['includes']['users'][0]['username'], 
                name=response['includes']['users'][0]['name'])
            author.save()
        
        # make the tweet
        t = Tweet.objects.create(
            id=response['data']['id'],author=author,
            created_at=parser.parse(response['data']['created_at']),
            text=response['data']['text'])
        t.save()

        # make the media if it has it
        if response['includes']['media']:
            url = 'url'
            if response['includes']['media'][0]['type'] == 'video':
                url = 'preview_image_url'

            # make a media object too
            media = Media.objects.create(
                tweet=t, 
                type=response['includes']['media'][0]['type'], 
                url = response['includes']['media'][0][url])
            media.save()

        # make the metrics
        tm = TweetMetrics.objects.create(
            tweet=t, 
            retweets=response['data']['public_metrics']['retweet_count'],
            replies=response['data']['public_metrics']['reply_count'],
            likes=response['data']['public_metrics']['like_count'],
            quotes=response['data']['public_metrics']['quote_count'])
        tm.save()

    else:
        print('existing tweet')
        # existing tweet
        # update the metrics
        Tweet.objects.filter(id=response['data']['id']).update(last_updated=now())
        tm = TweetMetrics.objects.create(
            tweet=t, 
            retweets=response['data']['public_metrics']['retweet_count'],
            replies=response['data']['public_metrics']['reply_count'],
            likes=response['data']['public_metrics']['like_count'],
            quotes=response['data']['public_metrics']['quote_count'])
        tm.save()
    return t

def parse_user_full(response):
    from .models import User, UserMetrics
    """
    Parses response from the /user/:id endpoint (a single fully fleshed out user json)
    Creates new user object or updates the existing one
    """
    defaults = {
        'id': response['data']['id'],
        'name': response['data']['name'],
        'username': response['data']['username'],
        'description': response['data']['description'],
        'verified': response['data']['verified'],
        'account_created': response['data']['created_at'],
        'last_updated': now()
    }
    
    defaults_metrics = {
        'user_id': response['data']['id'],
        'followers':response['data']['public_metrics']['followers_count'],
        'following': response['data']['public_metrics']['following_count'],
        'tweets:': response['data']['public_metrics']['tweet_count'],
        'listed':response['data']['public_metrics']['listed_count']
    }

    u, created = User.objects.update_or_create(id=response['data']['id'], defaults=defaults)
    UserMetrics.objects.update_or_create(user_id=response['data']['id'], defaults=defaults_metrics)
    return u