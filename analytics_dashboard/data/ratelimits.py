
'''
Rate limits per 15 minute window, by endpoint
'''
RATE_LIMITS = {
    '/tweets/:id': 300,
    '/tweets/:id/retweeted_by': 75,
    '/tweets/:id/liking_users': 75,
    '/users/:id/liked_tweets': 75,
    '/users/:id/followers': 15,
    '/users/:id/following': 15,
    '/users/:id': 300,

}

'''
Rate limits per 15 minute window, by limit
'''
RATE_LIMITS_BY_LIMIT = {
    300: ['/tweets/:id', '/users/:id'],
    75: ['/tweets/:id/retweeted_by', '/tweets/:id/liking_users', '/users/:id/liked_tweets'],
    15: ['/users/:id/followers', '/users/:id/following']
}