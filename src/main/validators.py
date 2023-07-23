from django.core.exceptions import ValidationError


def validate_link(value):
    if value[-1] == '/':
        raise ValidationError('ange utan efterföljande "/"')
