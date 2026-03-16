from django.urls import path
from .views import (PostListView, PostCreateView, PostDetailView, CommentListView, CommentCreateView,
                    CommentDeleteView, CommentLikeView, LikeView, FollowView, FollowerListView, FollowingListView)

urlpatterns = [
    path('posts/', PostListView.as_view(), name='post-list'),
    path('posts/create/', PostCreateView.as_view(), name='post-create'),
    path('posts/<uuid:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/<uuid:post_id>/comments/', CommentListView.as_view(), name='comment-list'),
    path('comments/create/', CommentCreateView.as_view(), name='comment-create'),
    path('comments/<uuid:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'),
    path('comments/<uuid:pk>/like/', CommentLikeView.as_view(), name='comment-like'),
    path('posts/<uuid:post_id>/like/', LikeView.as_view(), name='post-like'),
    path('users/<uuid:user_id>/follow/', FollowView.as_view(), name='follow'),
    path('users/<uuid:user_id>/followers/', FollowerListView.as_view(), name='followers'),
    path('users/<uuid:user_id>/following/', FollowingListView.as_view(), name='following'),
]