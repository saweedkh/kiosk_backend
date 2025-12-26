from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from apps.admin_panel.api.auth.auth_serializers import LoginSerializer, UserSerializer
from apps.logs.services.log_service import LogService

User = get_user_model()


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    
    def post(self, request):
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
    def post(self, request):
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
    serializer_class = UserSerializer
    
    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return Response(UserSerializer(request.user).data)

