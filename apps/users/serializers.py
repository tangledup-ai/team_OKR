"""
Serializers for User model
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Department


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'department', 'role',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器（管理员注册新成员）"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'department', 'role',
            'password', 'password_confirm', 'is_active'
        ]
        read_only_fields = ['id']
    
    def validate(self, attrs):
        """验证密码匹配"""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': '两次输入的密码不一致'
            })
        return attrs
    
    def validate_department(self, value):
        """验证部门选项"""
        if value not in dict(Department.choices):
            raise serializers.ValidationError(
                f'无效的部门选项。可选值: {", ".join(dict(Department.choices).keys())}'
            )
        return value
    
    def create(self, validated_data):
        """创建用户"""
        # Remove password_confirm from validated_data
        validated_data.pop('password_confirm', None)
        
        # Extract password
        password = validated_data.pop('password')
        
        # Set username to email (required by AbstractUser)
        validated_data['username'] = validated_data['email']
        
        # Create user
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新序列化器"""
    
    class Meta:
        model = User
        fields = [
            'name', 'department', 'role', 'is_active'
        ]
    
    def validate_department(self, value):
        """验证部门选项"""
        if value not in dict(Department.choices):
            raise serializers.ValidationError(
                f'无效的部门选项。可选值: {", ".join(dict(Department.choices).keys())}'
            )
        return value


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class UserDetailSerializer(serializers.ModelSerializer):
    """用户详情序列化器（包含更多信息）"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'department', 'role',
            'is_active', 'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']
