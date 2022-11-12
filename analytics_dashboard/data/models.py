from django.db import models

# Create your models here.
class User(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    username = models.CharField(max_length=15)
    description = models.CharField(max_length=100, blank=True, null=True)
    account_created = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(blank=True, null=True)
    verified = models.BooleanField(blank=True, null=True)
    def __str__(self):
        return self.username

class UserMetrics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='metrics', primary_key=True)
    followers = models.IntegerField()
    following = models.IntegerField()
    tweets = models.IntegerField()
    listed = models.IntegerField()

    def __str__(self):
        return self.user.username
    class Meta:
        verbose_name_plural = 'User Metrics'    

class UserFollowing(models.Model):
    user_id = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following_id = models.ForeignKey('User', related_name='followers', on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'following_id')
        verbose_name = 'Users Following'
        verbose_name_plural = "Users Following"

class Tweet(models.Model):
    id = models.BigIntegerField(primary_key=True)
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(blank=True, null=True)
    text = models.CharField(max_length=240, blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

class Media(models.Model):
    class MediaTypes(models.TextChoices):
        PHOTO = 'photo',
        VIDEO = 'video',
        GIF = 'animated_gif'
    tweet = models.OneToOneField(Tweet, on_delete=models.CASCADE, primary_key=True)
    type = models.CharField(max_length=12, choices=MediaTypes.choices, default=MediaTypes.PHOTO)
    url = models.URLField() # preview image for video, image url for gif/photo

    class Meta:
        verbose_name = 'Tweet Media'
        verbose_name_plural = 'Tweet Media'

class TweetMetrics(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='metrics')
    retweets = models.IntegerField()
    replies = models.IntegerField()
    likes = models.IntegerField()
    quotes = models.IntegerField()
    recorded_date = models.DateTimeField(auto_now_add=True)
    # add private metrics

    class Meta:
        verbose_name = 'Tweet Metrics'
        verbose_name_plural = 'Tweet Metrics'

class TweetRetweets(models.Model):
    tweet_id = models.ForeignKey(Tweet, related_name='retweeted', on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, related_name='retweets', on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tweet_id', 'user_id')
        verbose_name = 'Retweet'

class TweetLikes(models.Model):
    tweet_id = models.ForeignKey(Tweet, related_name='liked', on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, related_name='likes', on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tweet_id', 'user_id')
        verbose_name = 'Like'

class ApiTasks(models.Model):
    class TaskType(models.TextChoices):
        LIKING_USERS = 'liking_users',
        RETWEETS = 'retweets',
        TWEET_INFO = 'tweet_info',
        LIKED_TWEETS = 'liked_tweets',
        FOLLOWERS = 'followers',
        FOLLOWING = 'following',
        USER_LOOKUP = 'user_lookup'
    task_id = models.BigIntegerField()
    task = models.CharField(max_length=12, choices=TaskType.choices, default=TaskType.TWEET_INFO)
    args = models.CharField(max_length=30, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    hold_until = models.DateTimeField(blank=True, null=True)
    repeat_every = models.IntegerField(blank=True, null=True)
    class Meta:
        verbose_name_plural = 'API Tasks'