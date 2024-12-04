from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ValidationError
import re


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    


def check_required_fields(required_fields, request_data):    
    missing_fields = [field for field in required_fields if field not in request_data or not request_data[field]]

    if missing_fields:
        missing_fields_str = ", ".join(missing_fields)
        return f"{missing_fields_str} is required."
    return None


def validate_unique_email(model,value,instance):
    if value:
        if validate_email(value):
                return validate_email(value)
        if instance:
            if model.objects.filter(email=value).exclude(id=instance.id).exists():
                return f"This email already exists."
        elif model.objects.filter(email=value).exists():
            return f'This email already exists.'
    else:
        return None
    
    
def validate_email(email):
    # Define the pattern for email validation
    pattern = r'^([a-z0-9_\.-]+@[a-z0-9\.-]+\.[a-z\.]{2,6})$'
    
    # Check if the email is provided
    if not email:
        return 'Email is required!'
    # Check if the email length exceeds the maximum limit
    elif len(email) > 250:
        return 'Email must be less than or equal to 50 characters!'
    # Validate the email format using regex
    elif re.match(pattern, email) is None:
        return f"({email}) Invalid Email!"
    # elif User.objects.filter(email=email).exists():
    #     return f'Email({email}) already exists.'
    else:
        return None



Global_error_message = "Something went wrong!"



def flatten_errors(errors):
    flattened = {}
    for field, messages in errors.items():
        print("fields",field,"message",messages)
        if isinstance(messages, list) and len(messages) == 1:
            flattened[field] = messages[0]
        elif isinstance(messages, dict):
            for nested_field, nested_messages in messages.items():
                if isinstance(nested_messages, list) and len(nested_messages) == 1:
                    flattened[nested_field] = nested_messages[0]
                else:
                    flattened[nested_field] = nested_messages
        else:
            flattened[field] = messages
    for field, message in flattened.items():
        return f'{field}: {message}'
    
    
    
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png']
