from rest_framework import serializers, status
from .models import CustomUser, VIA_PHONE, VIA_EMAIL, CODE_VERIFY, DONE, PHOTO_DONE
from rest_framework.exceptions import ValidationError
from shared.utility import check_email_or_phone, check_email_or_phone_or_username
from django.db.models import Q
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_type = serializers.CharField(read_only=True)
    verify_type = serializers.CharField(read_only=True)

    def __init__(self, instance=None, data=..., **kwargs):
        super().__init__(instance, data, **kwargs)
        self.fields['email_or_phone'] = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'auth_status', 'verify_type']

    def create(self, validated_data):
        user = super().create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.generate_code(VIA_EMAIL)
            print(code)
        elif user.auth_type == VIA_PHONE:
            code = user.generate_code(VIA_PHONE)
            print(code)
        else:
            raise ValidationError('Email yoki telefon raqam xato')
        user.save()
        return user

    def validate(self, attrs):
        super().validate(attrs)
        data = self.auth_validate(attrs)
        return data

    @staticmethod
    def auth_validate(data):
        user_input = data.get('email_or_phone')
        user_input_type = check_email_or_phone(user_input)
        if user_input_type == "phone":
            data = {
                'auth_type': VIA_PHONE,
                'phone': user_input
            }
        elif user_input_type == 'email':
            data = {
                'auth_type': VIA_EMAIL,
                'email': user_input
            }
        else:
            raise ValidationError({
                'status': status.HTTP_400_BAD_REQUEST,
                'message': "Email yoki telefon raqamingiz xato kiritilgan."
            })
        return data

    def validate_email_or_phone(self, email_or_phone):
        user = CustomUser.objects.filter(
            Q(phone_number=email_or_phone) | Q(email=email_or_phone)
        )
        if user:
            raise ValidationError(detail='Bu telefon raqami bilan oldin royxatdan otilgan.')
        return email_or_phone

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['message'] = "Kodingiz yuborildi"
        data["refresh"] = instance.token()['refresh']
        data["access"] = instance.token()['access']
        return data


class UserChangeInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)

        if password is None or confirm_password is None or password != confirm_password:
            raise ValidationError({
                'message': "Parollar mos emas yoki xato kiritildi",
                'status': status.HTTP_400_BAD_REQUEST
            })
        if ' ' in password:
            raise ValidationError({
                'message': "Parol xato kiritildi",
                'status': status.HTTP_400_BAD_REQUEST
            })
        return data

    def validate_username(self, username):
        if len(username) < 6:
            raise ValidationError({'message': "Username kamida 7ta belgidan iborat bolishi kerak"})
        elif not username.isalnum():
            raise ValidationError({'message': "Usernameda ortiqcha belgi bolmasligi kerak"})
        elif username[0].isdigit():
            raise ValidationError({'message': "Username raqam bilan boshlanmasligi kerak"})
        return username

    def validate_first_name(self, first_name):
        first_name = first_name.strip()
        if not first_name:
            raise serializers.ValidationError("Ism bosh bolishi mumkin emas")
        if len(first_name) < 3:
            raise serializers.ValidationError("Ism kamida 3 belgidan iborat bolishi kerak")
        if len(first_name) > 50:
            raise serializers.ValidationError("Ism 50ta belgidan oshmasligi kerak")
        if not first_name.replace("'", "").isalpha():
            raise serializers.ValidationError("Ism faqat harflardan iborad bolishi kerak")
        return first_name.capitalize()

    def validate_last_name(self, last_name):
        last_name = last_name.strip()
        if not last_name:
            raise serializers.ValidationError("Familiya bosh bolishi mumkin emas")
        if len(last_name) < 3:
            raise serializers.ValidationError("Familiya kamida 3 belgidan iborat bolishi kerak")
        if len(last_name) > 50:
            raise serializers.ValidationError("Familiya 50ta belgidan oshmasligi kerak")
        if not last_name.isalpha():
            raise serializers.ValidationError("Familiya faqat harflardan iborad bolishi kerak")
        return last_name.capitalize()

    def update(self, instance, validated_data):
        if instance.auth_status != CODE_VERIFY:
            raise ValidationError({
                'message': "Siz hali tasdiqlanmagansiz",
                'status': status.HTTP_400_BAD_REQUEST
            })
        instance.first_name = validated_data.get('first_name')
        instance.last_name = validated_data.get('last_name')
        instance.username = validated_data.get('username')
        instance.set_password(validated_data.get('password'))
        instance.auth_status = DONE
        instance.save()
        return instance


class UserPhotoStatusSerializer(serializers.Serializer):
    photo = serializers.ImageField()

    def update(self, instance, validated_data):
        photo = validated_data.get('photo', None)
        if photo:
            instance.photo = photo
        if instance.auth_status == DONE:
            instance.auth_status = PHOTO_DONE
        instance.save()
        return instance


class LoginSerializer(TokenObtainPairSerializer):
    password = serializers.CharField(required=True, write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_input'] = serializers.CharField(required=True, write_only=True)
        self.fields['username'] = serializers.CharField(read_only=True, required=False)

    def validate(self, attrs):
        user = self.check_user_type(attrs)
        response_data = {
            'status': status.HTTP_200_OK,
            'message': "Siz tizimga kirdingiz",
            'access': user.token()['access'],
            'refresh': user.token()['refresh']
        }
        return response_data

    def check_user_type(self, data):
        password = data.get('password')
        user_input_data = data.get('user_input')
        user_type = check_email_or_phone_or_username(user_input_data)

        if user_type == "username":
            user = CustomUser.objects.filter(username=user_input_data).first()
            self.get_object(user)
            username = user_input_data

        elif user_type == 'email':
            user = CustomUser.objects.filter(email__icontains=user_input_data.lower()).first()
            self.get_object(user)
            username = user.username

        elif user_type == 'phone':
            user = CustomUser.objects.filter(phone_number=user_input_data).first()
            self.get_object(user)
            username = user.username
        else:
            raise ValidationError(detail='Malumot topilmadi')

        if user.auth_status not in [DONE, PHOTO_DONE]:
            raise ValidationError(detail="Siz toliq royxatdan otmagansiz")

        authentication_kwargs = {
            "password": password,
            self.username_field: username
        }

        user = authenticate(**authentication_kwargs)
        if not user:
            raise ValidationError('Parol xato')
        return user

    def get_object(self, user):
        if not user:
            raise ValidationError({
                'message': "Login xato kiritingiz",
                'status': status.HTTP_400_BAD_REQUEST
            })
        return True


class ForgotPassword(serializers.Serializer):
    user_input = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        user_data = attrs.get('user_input', None)
        if not user_data:
            raise ValidationError('Email, telefon raqam yoki username kiriting')

        user_data_type = check_email_or_phone_or_username(user_data)
        user = CustomUser.objects.filter(
            Q(username=user_data) | Q(email=user_data) | Q(phone_number=user_data)
        ).first()

        if not user:
            raise ValidationError('Email, telefon raqam yoki username xato kiritilgan')

        if user_data_type == 'username':
            if user.email:
                code = user.generate_code(VIA_EMAIL)
                print('Email Code :::::::::::', code)
            elif user.phone_number:
                code = user.generate_code(VIA_PHONE)
                print('Phone Code :::::::::::', code)
            else:
                raise ValidationError("Toliq royxatdan otmagansiz")

        elif user_data_type == 'email':
            code = user.generate_code(VIA_EMAIL)
            print('Email Code :::::::::::', code)

        elif user_data_type == 'phone':
            code = user.generate_code(VIA_PHONE)
            print('Phone Code :::::::::::', code)

        attrs['user'] = user
        return attrs


class ResetPassword(serializers.Serializer):
    pass