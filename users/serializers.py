# serializers.py

from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import User
from .register import register_social_user
from rest_framework.exceptions import AuthenticationFailed
from . import google
import os
import re

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'first_name', 'last_name', 'gender', 'city', 'address', 'image', 'password']

    # Image validation
    def validate_image(self, value):
        # List of allowed file extensions
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        
        # Get the file extension of the uploaded image
        ext = os.path.splitext(value.name)[1].lower()  # Extract the file extension
        
        # Check if the file extension is valid
        if ext not in valid_extensions:
            raise ValidationError(f'Unsupported file extension "{ext}". Allowed extensions are: {", ".join(valid_extensions)}.')
        
        return value

    def create(self, validated_data):
        # Create the user instance
        user = User(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            gender=validated_data['gender'],
            city=validated_data.get('city', ''),
            address=validated_data.get('address', ''),
            image=validated_data.get('image', None),
        )
        # Set the user's password
        user.set_password(validated_data['password'])
        user.save()
        return user

class LoginSerializers(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "phone_number",
            "password",
        ]

    def create(self, validated_data):
        return super(LoginSerializers, self).create(validated_data)


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'first_name', 'last_name', 'gender']


class PasswordValidatorMixin:
    def validate_password(self, password):
        """ Validates password complexity. """
        if len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'\d', password):
            raise serializers.ValidationError("Password must contain at least one digit.")
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[\W_]', password):  # Matches any special character
            raise serializers.ValidationError("Password must contain at least one special character.")
        return password


class PasswordChangeSerializer(serializers.Serializer, PasswordValidatorMixin):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')

        if new_password != confirm_new_password:
            raise serializers.ValidationError("New password and confirm new password do not match.")

        # Use the mixin method to validate password complexity
        self.validate_password(new_password)

        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer, PasswordValidatorMixin):
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        new_password = data.get('new_password')
        confirm_new_password = data.get('confirm_new_password')

        if new_password != confirm_new_password:
            raise serializers.ValidationError("Passwords do not match.")

        # Use the mixin method to validate password complexity
        self.validate_password(new_password)

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'gender', 'city', 'address', 'image']

    def validate_image(self, value):
        # List of allowed file extensions
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        
        # Get the file extension of the uploaded image
        ext = os.path.splitext(value.name)[1].lower()  # Extract the file extension
        
        # Check if the file extension is valid
        if ext not in valid_extensions:
            raise ValidationError(f'Unsupported file extension "{ext}". Allowed extensions are: {", ".join(valid_extensions)}.')
        
        return value

    def update(self, instance, validated_data):
        # If a new image is provided, delete the old image
        if 'image' in validated_data and instance.image:
            instance.image.delete(save=False)  # Delete the old image from storage

        return super().update(instance, validated_data)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class GoogleSocialAuthSerializer(serializers.Serializer):
    auth_token = serializers.CharField()

    def validate_auth_token(self, auth_token):
        user_data = google.Google.validate(auth_token)
        try:
            user_data['sub']
        except:
            raise serializers.ValidationError(
                'The token is invalid or expired. Please login again.'
            )

        if user_data['aud'] != os.environ.get('GOOGLE_CLIENT_ID'):

            raise AuthenticationFailed('oops, who are you?')

        user_id = user_data['sub']
        email = user_data['email']
        name = user_data['name']
        provider = 'google'

        return register_social_user(
            provider=provider, user_id=user_id, email=email, name=name)


class ContactUsSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20, required=False)
    message = serializers.CharField()