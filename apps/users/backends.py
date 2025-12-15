"""
Custom authentication backend for email-based authentication
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    自定义认证后端，使用邮箱而不是用户名进行认证
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        使用邮箱和密码进行认证
        username参数实际上接收的是email
        """
        try:
            # Try to fetch the user by email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None
        
        # Check the password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        根据用户ID获取用户
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
