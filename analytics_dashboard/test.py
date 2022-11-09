import json

f = open('tweet_picture.json')
response = json.load(f)

print(response['includes']['media'][0]['type'])