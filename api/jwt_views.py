from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.conf import settings


def set_jwt_cookies(response, access_token, refresh_token):
    """Helper to set both tokens as httpOnly cookies"""
    response.set_cookie(
        key='access_token',
        value=str(access_token),
        httponly=True,
        secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
        samesite='Lax',
        max_age=60 * 60,  # 1 hour
    )
    response.set_cookie(
        key='refresh_token',
        value=str(refresh_token),
        httponly=True,
        secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
        samesite='Lax',
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    return response


class JWTLoginView(APIView):
    """
    POST /api/v1/auth/login/
    Body: { "email": "...", "password": "..." }
    Returns: user data + sets httpOnly JWT cookies
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '').strip()

        if not email or not password:
            return Response(
                {'error': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate using email as username
        user = authenticate(request, username=email, password=password)

        if not user:
            return Response(
                {'error': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is disabled.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response = Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'access_token': str(access),    # also return in body for flexibility
            'refresh_token': str(refresh),
        }, status=status.HTTP_200_OK)

        # Set httpOnly cookies
        set_jwt_cookies(response, access, refresh)
        return response


class JWTRefreshView(APIView):
    """
    POST /api/v1/auth/refresh/
    Reads refresh token from cookie, returns new access token
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'error': 'No refresh token found.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            refresh = RefreshToken(refresh_token)
            access = refresh.access_token

            response = Response({
                'message': 'Token refreshed',
                'access_token': str(access),
            })
            # Set new access cookie
            response.set_cookie(
                key='access_token',
                value=str(access),
                httponly=True,
                secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
                samesite='Lax',
                max_age=60 * 60,
            )
            return response

        except TokenError:
            return Response(
                {'error': 'Invalid or expired refresh token. Please login again.'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class JWTLogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists refresh token + clears cookies
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()  # blacklist so it can't be reused
            except TokenError:
                pass  # already invalid, that's fine

        response = Response({'message': 'Logged out successfully.'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


class JWTRegisterView(APIView):
    """
    POST /api/v1/auth/register/
    Body: { "username": "...", "email": "...", "password": "...", "password2": "..." }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from accounts.models import CustomUser, Workspace
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        username = request.data.get('username', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')
        password2 = request.data.get('password2', '')

        # Validations
        if not all([username, email, password, password2]):
            return Response({'error': 'All fields are required.'}, status=400)

        if password != password2:
            return Response({'error': 'Passwords do not match.'}, status=400)

        if CustomUser.objects.filter(email=email).exists():
            return Response({'error': 'Email already registered.'}, status=400)

        if CustomUser.objects.filter(username=username).exists():
            return Response({'error': 'Username already taken.'}, status=400)

        try:
            validate_password(password)
        except ValidationError as e:
            return Response({'error': list(e.messages)}, status=400)

        # Create user
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        Workspace.objects.create(owner=user, name=f"{username}'s Workspace")

        # Auto login — generate tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response = Response({
            'message': 'Account created successfully!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'access_token': str(access),
            'refresh_token': str(refresh),
        }, status=status.HTTP_201_CREATED)

        set_jwt_cookies(response, access, refresh)
        return response


class WhoAmIView(APIView):
    """
    GET /api/v1/auth/me/
    Returns current authenticated user info
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'bio': user.bio,
            'created_at': user.created_at,
        })