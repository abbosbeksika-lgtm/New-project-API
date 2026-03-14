from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView, status
from rest_framework import permissions
from .models import CustomUser, NEW, CODE_VERIFY, DONE, PHOTO_DONE, VIA_PHONE, VIA_EMAIL
from .serializers import (SignUpSerializer, UserChangeInfoSerializer, UserPhotoStatusSerializer, LoginSerializer,\
                           ForgotPassword, ResetPassword)
from datetime import datetime
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from shared.utility import send_email_code, send_sms_code



class SignUpView(CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignUpSerializer
    queryset = CustomUser.objects.all()

class CodeVerifyView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        code = self.request.data.get('code')
        codes = user.verify_codes.filter(
            code=code,
            expiration_time__gte=datetime.now(),
            is_active=False
        )
        if not codes.exists():
            raise ValidationError({
                "message": "Kodingiz xato yoki eskirgan",
                "status": status.HTTP_400_BAD_REQUEST
            })
        codes.update(is_active=True)

        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFY
            user.save()

        return Response({
            'message': "Kodingiz tasdiqlandi",
            'status': status.HTTP_200_OK,
            'access': user.token()['access'],
            'refresh': user.token()['refresh']
        })

class GetNewCodeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        code = user.verify_codes.filter(expiration_time__gte=datetime.now(), is_active=False)
        if code.exists():
            raise ValidationError({
                "message": "Sizda hali kod bor",
                "status": status.HTTP_400_BAD_REQUEST
            })

        if user.auth_type == VIA_EMAIL:
            code = user.generate_code(VIA_EMAIL)
            send_email_code(user.email, code)

        elif user.auth_type == VIA_PHONE:
            code = user.generate_code(VIA_PHONE)
            send_sms_code(user.phone_number, code)

        return Response({
            'message': "Kod yuborildi",
            'status': status.HTTP_201_CREATED,
        })

class UserChangeInfoView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request):
        user = request.user
        serializer = UserChangeInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=user, validated_data=serializer.validated_data)

        return Response({
            'message': "Malumotlaringiz qoshildi",
            'status': status.HTTP_200_OK,
            'access': user.token()['access'],
            'refresh': user.token()['refresh']
        })

class UserPhotoStatusView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request):
        user = request.user
        serializer = UserPhotoStatusSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=user, validated_data=serializer.validated_data)

        return Response({
            'message': "Rasm qoshildi",
            'status': status.HTTP_200_OK,
            'access': user.token()['access'],
            'refresh': user.token()['refresh']
        })

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        refresh = request.data.get('refresh', None)
        if not refresh:
            raise ValidationError({
                'message': "Refresh token kerak",
                'status': status.HTTP_400_BAD_REQUEST
            })
        try:
            refresh_token = RefreshToken(refresh)
            refresh_token.blacklist()
        except Exception as e:
            raise ValidationError(detail=f'Xatolik: {e}')

        return Response({
            'status': status.HTTP_200_OK,
            'message': 'Tizimdan chiqdingiz'
        })

class LoginRefresh(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        refresh = request.data.get('refresh', None)
        if not refresh:
            raise ValidationError({
                'message': "Refresh token kerak",
                'status': status.HTTP_400_BAD_REQUEST
            })
        try:
            refresh_token = RefreshToken(refresh)
        except Exception as e:
            raise ValidationError(detail=f"Xatolik: {e}")
        else:
            response_data = {
                'status':status.HTTP_201_CREATED,
                'access': refresh_token.access_token
            }

            return Response(response_data)

class ForgotPassword(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = ForgotPassword(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get('user')
        if user.email:
            code = user.generate_code(VIA_EMAIL)
            send_email_code(user.email, code)

        elif user.phone_number:
            code = user.generate_code(VIA_PHONE)
            send_sms_code(user.phone_number, code)

        return Response({
            'status': status.HTTP_200_OK,
            'message': "Tasdiqlash kodi yuborildi"
        })


class ResetPassword(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        user_input = request.data.get('user_input', None)
        if not user_input:
            raise ValidationError({
                'message': "user_input maydoni kerak",
                'status': status.HTTP_400_BAD_REQUEST
            })

        user = CustomUser.objects.filter(Q(username=user_input) | Q(email=user_input) | Q(phone_number=user_input)).first()

        if not user:
            raise ValidationError({
                'message': "Foydalanuvchi topilmadi",
                'status': status.HTTP_400_BAD_REQUEST
            })

        code = request.data.get('code', None)
        verify = user.verify_codes.filter(code=code, expiration_time__gte=datetime.now(), is_active=False).first()

        if not verify:
            raise ValidationError({
                'message': "Kod xato yoki eskirgan",
                'status': status.HTTP_400_BAD_REQUEST
            })

        verify.is_active = True
        verify.save()

        serializer = ResetPassword(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=user, validated_data=serializer.validated_data)

        return Response({
            'status': status.HTTP_200_OK,
            'message': "Parolingiz yangilandi",
            'access': user.token()['access'],
            'refresh': user.token()['refresh']
        })