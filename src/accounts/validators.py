from django.core.validators import RegexValidator


validate_ipaddress = RegexValidator(
    regex=r'^\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}$',
    message='The IP address must be minimum 7 characters, maximum 15 characters. for example: 123.123.123.123'
)


first_part_validate_ipaddress = RegexValidator(
    regex=r'^\d{1,3}[.]\d{1,3}[.]\d{1,3}$',
    message='The IP address must be minimum 5 characters, maximum 11 characters. for example: 123.123.123'
)
