from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Post, Comment, CommentLike, Like, Follow, Story, StoryView


User = get_user_model()


class PostSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    like_count = serializers.ReadOnlyField()
    comment_count = serializers.ReadOnlyField()

    class Meta:
        model = Post
        fields = ['id', 'user', 'image', 'title', 'desc', 'like_count', 'comment_count', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'text', 'parent', 'replies', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []

    def validate_post(self, post):
        if not Post.objects.filter(id=post.id).exists():
            raise ValidationError({'message': "Post topilmadi"})
        return post


class CommentLikeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CommentLike
        fields = ['id', 'user', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class LikeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def validate(self, attrs):
        user = self.context['request'].user
        post = attrs.get('post')
        if Like.objects.filter(user=user, post=post).exists():
            raise ValidationError({'message': "Siz allaqachon like bosdingiz"})
        return attrs


class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.StringRelatedField(read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'following_username', 'created_at']
        read_only_fields = ['id', 'follower', 'created_at']

    def validate(self, attrs):
        follower = self.context['request'].user
        following = attrs.get('following')

        if follower == following:
            raise ValidationError({'message': "O'zingizni follow qila olmaysiz"})
        if Follow.objects.filter(follower=follower, following=following).exists():
            raise ValidationError({'message': "Siz allaqachon follow qilgansiz"})
        return attrs


class FollowerListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='follower.username', read_only=True)
    photo = serializers.ImageField(source='follower.photo', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'username', 'photo', 'created_at']


class FollowingListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='following.username', read_only=True)
    photo = serializers.ImageField(source='following.photo', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'username', 'photo', 'created_at']
