from django.contrib import admin
from django.urls import path
from .views import register, login, refresh_token, create_post, get_post, follow, follow_list, newsfeed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('refresh/', refresh_token, name='refresh_token'),
    path('posts/', create_post, name='create_post'),
    path('posts/<int:post_id>/', get_post, name='get_post'),
    path('follow/', follow, name='follow'),
    path('follow/<int:user_id>/', follow_list, name='follow_list'),
    path('newsfeed/', newsfeed, name='newsfeed'),
]

