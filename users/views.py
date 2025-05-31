from django.contrib.auth import authenticate
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .serializers import UserRegistrationSerializer, LoginSerializers, UserListSerializer, PasswordChangeSerializer, PasswordResetConfirmSerializer, UserProfileSerializer, PasswordResetRequestSerializer, GoogleSocialAuthSerializer, ContactUsSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import GenericAPIView
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class UserRegistrationView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "user": serializer.data,
            "message": "User created successfully"
        }, status=status.HTTP_201_CREATED)


class UserLoginView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializers

    def post(self, request):
        phone_number = request.data.get("phone_number", None)
        email = request.data.get("email", None)
        password = request.data.get("password", None)

        # Ensure either phone number or email is provided
        if not phone_number and not email:
            return Response(
                {"message": "Either phone number or email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not password:
            return Response(
                {"message": "Please enter your password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for the provided contact method (phone or email)
        user = None
        if phone_number:
            user = User.objects.filter(phone_number__iexact=phone_number).first()
        elif email:
            user = User.objects.filter(email__iexact=email).first()

        # Verify Password
        if user:
            VerifyUser = authenticate(request, username=user.email, password=password)
            if VerifyUser:
                user_data = UserProfileSerializer(user).data
                return Response(
                    {
                        "detail": get_tokens_for_user(user),
                        "user": user_data,
                        "message": "User logged in successfully",
                    },
                    status=status.HTTP_202_ACCEPTED,
                )
            else:
                return Response(
                    {"message": "Invalid login credentials."}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class UserListView(generics.ListAPIView):
    """API view to retrieve list of users, accessible only by admin users."""
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]


class PasswordChangeView(generics.UpdateAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.get_object()
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()

        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{settings.DOMAIN}/user/password-reset-confirm/{uid}/{token}/"

            # Send the email
            subject = 'Password Reset Request'
            msg_plain = render_to_string('email.txt', {'reset_link': reset_link, 'email': user.email})
            email_template = render_to_string('password_reset_email.html', {'reset_link': reset_link, 'email': user.email})
            send_mail(
                subject,
                msg_plain,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=email_template,
            )

            return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)

        return Response({"message": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        uidb64 = kwargs.get('uidb64')
        token = kwargs.get('token')

        # Decode the UID and retrieve the user
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        print(f"Decoded UID: {uid}, User: {user}, Token: {token}")

        if user is not None:
            is_token_valid = default_token_generator.check_token(user, token)
            print(f"Token valid: {is_token_valid}")

            if is_token_valid:
                # Process password reset
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                # Set new password
                user.set_password(serializer.validated_data['new_password'])
                user.save()

                return Response({"message": "Password has been reset."}, status=status.HTTP_200_OK)
            else:
                print("Invalid token")
        
        return Response({"message": "Invalid reset token or user."}, status=status.HTTP_400_BAD_REQUEST)


class UserDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, *args, **kwargs):
        try:
            # Retrieve the user to be deleted
            user_to_delete = User.objects.get(pk=kwargs.get('pk'))

            # Restrict non-admin users from deleting other users
            if not request.user.is_site_admin and request.user.pk != user_to_delete.pk:
                return Response(
                    {"message": "You do not have permission to delete this user."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Delete the user
            user_to_delete.delete()
            return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Fetch the user's profile
        return self.request.user

    def put(self, request, *args, **kwargs):
        # Update the user profile
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        # Partial update of the user profile
        return self.partial_update(request, *args, **kwargs)


class GoogleSocialAuthView(GenericAPIView):

    serializer_class = GoogleSocialAuthSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = ((serializer.validated_data)['auth_token'])
        return Response(data, status=status.HTTP_200_OK)
    

class ContactUsAPIView(APIView):
    def post(self, request):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            first_name = serializer.validated_data['first_name']
            last_name = serializer.validated_data['last_name']
            email = serializer.validated_data['email']
            phone_number = serializer.validated_data.get('phone_number', 'Not provided')
            message = serializer.validated_data['message']

            # Construct the email message
            subject = f"New Contact Us Message from {first_name} {last_name}"
            admin_message = (
                f"New contact request received:\n\n"
                f"Name: {first_name} {last_name}\n"
                f"Email: {email}\n"
                f"Phone Number: {phone_number}\n"
                f"Message:\n{message}"
            )

            try:
                send_mail(
                    subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACTUS_EMAIL],
                    fail_silently=False,
                )
                return Response({"message": "Contact request sent successfully!"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"message": "Failed to send email. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)