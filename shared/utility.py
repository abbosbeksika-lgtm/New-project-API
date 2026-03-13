import re
from rest_framework import status
from rest_framework.exceptions import ValidationError

email_regex = re.compile(r'[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+')
phone_regex = re.compile(r'^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$')
username_regex = re.compile(r'^[a-z0-9_-]{3,15}$')

def check_email_or_phone(user_input):
    if re.fullmatch(email_regex, user_input):
        return 'email'

    elif re.fullmatch(phone_regex, user_input):
        return 'phone'

    else:
        raise ValidationError( {
            'status': status.HTTP_400_BAD_REQUEST,
            'message': "Email yoki telefon raqamingizni xato kiritdingiz."
        })

def check_email_or_phone_or_username(user_input):
    if re.fullmatch(email_regex, user_input):
        return 'email'

    elif re.fullmatch(phone_regex, user_input):
        return 'phone'

    elif re.fullmatch(username_regex, user_input):
        return 'username'

    else:
        raise ValidationError( {
            'status': status.HTTP_400_BAD_REQUEST,
            'message': "Login xato kiritdingiz."
        })
