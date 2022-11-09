from django.contrib import admin
from .models import *

# Register your models here.

class UserMetricsInline(admin.StackedInline):
    model = UserMetrics

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'name')
    inlines = [UserMetricsInline, ]

@admin.register(ApiTasks)
class ApiTasksAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'args', 'created', 'hold_until')

@admin.register(TweetMetrics)
class TweetMetricsAdmin(admin.ModelAdmin):
    list_display = ('tweet', 'recorded_date')

admin.site.register(UserFollowing)
admin.site.register(UserMetrics)
admin.site.register(Tweet)
admin.site.register(Media)
admin.site.register(TweetLikes)
admin.site.register(TweetRetweets)
admin.site.register(WatchedTweets)
admin.site.register(WatchedUsers)