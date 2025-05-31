import os
import uuid
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

def validate_file_size(value):
    filesize = value.size
    if filesize >= 1024 * 1024 * settings.MAX_FILE_SIZE:
        raise ValidationError(
            f"Image file size should be less than {settings.MAX_FILE_SIZE}MB"
        )


def get_profile_upload_path(instance, filename):
    now = datetime.now()
    unique_id = uuid.uuid4().hex
    basename, extension = os.path.splitext(filename)
    return os.path.join(
        f"{instance.user_type}".lower(),
        f"{instance.first_name}".lower(),
        "profile",
        "{date}-{unique_id}{extension}".format(
            date=now.strftime("%Y-%m-%d_%H-%M-%S"),
            unique_id=unique_id,
            extension=extension,
        ),
    )


def get_product_upload_path(instance, filename):
    now = datetime.now()
    unique_id = uuid.uuid4().hex
    basename, extension = os.path.splitext(filename)
    return os.path.join(
        "product",
        f"{instance.product.id}".lower(),
        "{date}-{unique_id}{extension}".format(
            date=now.strftime("%Y-%m-%d_%H-%M-%S"),
            unique_id=unique_id,
            extension=extension,
        ),
    )

def get_product_image_upload_path(instance, filename):
    # Use the product's ID and color to create a unique path
    return f"product/{instance.id}/images/{filename}"

def superuser_required(func):
    """ Custom decorator to ensure that only superusers can access the view. """
    @wraps(func)
    def wrapped_view(self, request, *args, **kwargs):
        # Apply the IsAuthenticated permission
        permission = IsAuthenticated()
        if not permission.has_permission(request, self):
            return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if the user is a superuser
        if not request.user.is_superuser:
            return Response({"error": "Only superusers can perform this action."}, status=status.HTTP_403_FORBIDDEN)
        
        # Proceed to the view function if the user is authenticated and a superuser
        return func(self, request, *args, **kwargs)

    return wrapped_view
