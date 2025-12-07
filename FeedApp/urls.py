from django.urls import path
from . import views

app_name = 'FeedApp'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('myfeed', views.myfeed, name='myfeed'),
    path('friendsfeed/', views.friendsfeed, name='friendsfeed'),
    path('new_post/', views.new_post, name='new_post'),
    path('comments/<int:post_id>/', views.comments, name='comments'),
    path('friends/', views.friends, name='friends'),
    ]

    