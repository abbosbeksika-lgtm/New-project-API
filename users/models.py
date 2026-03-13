from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from shared.models import BaseModel
from datetime import datetime, timedelta
from config.settings import EMAIL_EXPIRATION_TIME, PHONE_EXPIRATION_TIME
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
import random

ORDINARY_USER, ADMIN, MANAGER = ('ordinary_user', 'admin', 'manager')
NEW, CODE_VERIFY, DONE, PHOTO_DONE = ('new', 'code_verify', 'done', 'photo_done')
VIA_EMAIL, VIA_PHONE = ('via_email', 'via_phone')


class CustomUser(AbstractUser, BaseModel):
    USER_ROLE = (
        (ORDINARY_USER, ORDINARY_USER),
        (ADMIN, ADMIN),
        (MANAGER, MANAGER)
    )

    USER_AUTH_STATUS = (
    (NEW, NEW),
    (CODE_VERIFY, CODE_VERIFY),
    (DONE, DONE),
    (PHOTO_DONE, PHOTO_DONE)
    )

    USER_AUTH_TYPE = (
    (VIA_EMAIL, VIA_EMAIL),
    (VIA_PHONE, VIA_PHONE)
    )

    user_role = models.CharField(max_length=20, choices=USER_ROLE, default=ORDINARY_USER)
    auth_status = models.CharField(max_length=20, choices=USER_AUTH_STATUS, default=NEW)
    auth_type = models.CharField(max_length=20, choices=USER_AUTH_TYPE)
    email = models.EmailField(max_length=50, blank=True,null=True , unique=True)
    phone_number = models.CharField(max_length=13, blank=True, null=True, unique=True)
    photo = models.ImageField(upload_to='user_photos/', validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'heic'])])

    def __str__(self):
        return self.username

    def check_username(self):
        if not self.username:
            temp_username = f'username{uuid.uuid4().__str__().split('-')[-1]}'
            user = CustomUser.objects.filter(username=temp_username).first()
            if user:
                while user.exists():
                    temp_username += str(random.randint(0,9))

            self.username = temp_username

    def set_temp_pass(self, raw_password):
        if not self.password:
            temp_password = f"pass{uuid.uuid4().__str__().split('-')[-1]}"

            self.password = temp_password

    def hashing_pass(self):
        if self.password.startswith('pbkdf2_sha256'):
            self.password = self.set_password(self.password)

    def check_email(self):
        if self.email:
            email_normalize = self.email.lower()
            self.email = email_normalize


    def token(self):
        refresh_token = RefreshToken.for_user(self)

        data = {
            'refresh': str(refresh_token),
            'access': str(refresh_token.access_token)
        }
        return data

    def generate_code(self, verify_type):
        code = random.randint(1000,9999)
        CodeVerify.objects.create(
            code=code,
            user=self,
            verify_type=verify_type
        )
        return code

    def save( self, *args, **kwargs):
        self.check_email()
        self.check_username()
        self.set_temp_pass()
        super().save(*args, **kwargs)


class CodeVerify(BaseModel):
    VERIFY_TYPE = (
    (VIA_EMAIL, VIA_EMAIL),
    (VIA_PHONE, VIA_PHONE)
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verify_codes')
    code = models.CharField(max_length=4)
    verify_type = models.CharField(max_length=30, choices=VERIFY_TYPE)
    expiration_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.verify_type == VIA_EMAIL:
            self.expiration_time = datetime.now() + timedelta(minutes=EMAIL_EXPIRATION_TIME)
        else:
            self.expiration_time = datetime.now() + timedelta(minutes=PHONE_EXPIRATION_TIME)
        super().save()

    def __str__(self):
        return f"{self.user.username} | {self.code}"

