from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import get_user_model
from .models import Post, Comment, CommentLike, Like, Follow
from .serializers import (PostSerializer, CommentSerializer, FollowerListSerializer, FollowingListSerializer)

User = get_user_model()


class PostListView(ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PostSerializer
    queryset = Post.objects.all().order_by('-created_at')


class PostCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = PostSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({
            'status': status.HTTP_201_CREATED,
            'message': "Post yaratildi",
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, pk):
        try:
            return Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            raise ValidationError({'message': "Post topilmadi"})

    def get(self, request, pk):
        post = self.get_object(pk)
        serializer = PostSerializer(post)
        return Response(serializer.data)

    def put(self, request, pk):
        post = self.get_object(pk)
        if post.user != request.user:
            raise ValidationError({'message': "Bu post sizniki emas"})
        serializer = PostSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'status': status.HTTP_200_OK,
            'message': "Post yangilandi",
            'data': serializer.data
        })

    def delete(self, request, pk):
        post = self.get_object(pk)
        if post.user != request.user:
            raise ValidationError({'message': "Bu post sizniki emas"})
        post.delete()
        return Response({
            'status': status.HTTP_204_NO_CONTENT,
            'message': "Post o'chirildi"
        }, status=status.HTTP_204_NO_CONTENT)


class CommentListView(ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CommentSerializer

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id, parent=None).order_by('-created_at')


class CommentCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = CommentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({
            'status': status.HTTP_201_CREATED,
            'message': "Komment qo'shildi",
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            raise ValidationError({'message': "Komment topilmadi"})

        if comment.user != request.user:
            raise ValidationError({'message': "Bu komment sizniki emas"})

        comment.delete()
        return Response({
            'status': status.HTTP_204_NO_CONTENT,
            'message': "Komment o'chirildi"
        }, status=status.HTTP_204_NO_CONTENT)


class CommentLikeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            raise ValidationError({'message': "Komment topilmadi"})

        like = CommentLike.objects.filter(user=request.user, comment=comment)
        if like.exists():
            like.delete()
            return Response({
                'status': status.HTTP_200_OK,
                'message': "Like olib tashlandi"
            })

        CommentLike.objects.create(user=request.user, comment=comment)
        return Response({
            'status': status.HTTP_201_CREATED,
            'message': "Kommentga like bosildi"
        }, status=status.HTTP_201_CREATED)


class LikeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, post_id):
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            raise ValidationError({'message': "Post topilmadi"})

        like = Like.objects.filter(user=request.user, post=post)
        if like.exists():
            like.delete()
            return Response({
                'status': status.HTTP_200_OK,
                'message': "Like olib tashlandi"
            })

        Like.objects.create(user=request.user, post=post)
        return Response({
            'status': status.HTTP_201_CREATED,
            'message': "Like bosildi"
        }, status=status.HTTP_201_CREATED)


class FollowView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, user_id):
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError({'message': "Foydalanuvchi topilmadi"})

        if target_user == request.user:
            raise ValidationError({'message': "O'zingizni follow qila olmaysiz"})

        follow = Follow.objects.filter(follower=request.user, following=target_user)
        if follow.exists():
            follow.delete()
            return Response({
                'status': status.HTTP_200_OK,
                'message': "Unfollow qilindi"
            })

        Follow.objects.create(follower=request.user, following=target_user)
        return Response({
            'status': status.HTTP_201_CREATED,
            'message': "Follow qilindi"
        }, status=status.HTTP_201_CREATED)


class FollowerListView(ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FollowerListSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Follow.objects.filter(following_id=user_id).order_by('-created_at')


class FollowingListView(ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FollowingListSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Follow.objects.filter(follower_id=user_id).order_by('-created_at')

