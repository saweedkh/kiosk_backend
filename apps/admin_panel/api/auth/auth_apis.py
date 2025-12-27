from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from apps.admin_panel.api.auth.auth_serializers import LoginSerializer, UserSerializer
from apps.logs.services.log_service import LogService
from apps.core.api.schema import custom_extend_schema
from apps.core.api.parameter_serializers import LoginRequestSerializer
from apps.core.api.status_codes import ResponseStatusCodes

User = get_user_model()


class LoginAPIView(generics.GenericAPIView):
    """
    API endpoint for admin login.
    
    Authenticates admin user and creates a session.
    """
    serializer_class = LoginSerializer
    
    @custom_extend_schema(
        resource_name="AdminLogin",
        parameters=[LoginRequestSerializer],
        request_serializer=LoginSerializer,
        response_serializer=UserSerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.BAD_REQUEST,
            ResponseStatusCodes.UNAUTHORIZED,
        ],
        summary="Admin Login",
        description="Authenticate admin user and create a session. Returns user information on successful login.",
        tags=["Admin - Auth"],
        operation_id="admin_login"
    )
    def post(self, request):
        """
        Authenticate and login admin user.
        
        Args:
            request: HTTP request object with username and password
            
        Returns:
            Response: Success message and user data
            
        Raises:
            ValidationError: If credentials are invalid
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        login(request, user)
        
        LogService.log_info(
            'admin',
            'admin_login',
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'username': user.username}
        )
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data
        })


class LogoutAPIView(generics.GenericAPIView):
    """
    API endpoint for admin logout.
    
    Logs out the current admin user and destroys the session.
    """
    @custom_extend_schema(
        resource_name="AdminLogout",
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.UNAUTHORIZED,
        ],
        summary="Admin Logout",
        description="Logout the current admin user and destroy the session.",
        tags=["Admin - Auth"],
        operation_id="admin_logout"
    )
    def post(self, request):
        """
        Logout admin user.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Success message
        """
        if request.user.is_authenticated:
            username = request.user.username
            logout(request)
            
            LogService.log_info(
                'admin',
                'admin_logout',
                user=request.user if hasattr(request, 'user') else None,
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'username': username}
            )
        
        return Response({'message': 'Logout successful'})


class UserInfoAPIView(generics.GenericAPIView):
    """
    API endpoint for getting current admin user information.
    
    Returns information about the currently authenticated admin user.
    """
    serializer_class = UserSerializer
    
    @custom_extend_schema(
        resource_name="AdminUserInfo",
        response_serializer=UserSerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.UNAUTHORIZED,
        ],
        summary="Get Current User Info",
        description="Get information about the currently authenticated admin user.",
        tags=["Admin - Auth"],
        operation_id="admin_user_info"
    )
    def get(self, request):
        """
        Get current admin user information.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: User data
            
        Raises:
            401: If user is not authenticated or not staff
        """
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return Response(UserSerializer(request.user).data)

