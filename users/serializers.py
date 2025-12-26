# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import CustomUser, UserActivityLog, UserVerification
import re


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type', 
                 'verification_status', 'date_joined', 'last_login', 'profile_image',
                 'organization', 'country', 'city', 'contribution_score']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        exclude = ['password', 'is_superuser', 'is_staff', 'is_deleted', 'deleted_at']
        read_only_fields = ['uuid', 'date_joined', 'last_login', 'last_activity', 'login_count']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.'
        }
    )
    confirm_password = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    role = serializers.CharField(write_only=True, required=True)
    terms = serializers.BooleanField(write_only=True, required=True)
    newsletter = serializers.BooleanField(write_only=True, required=False, default=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'confirm_password', 
            'first_name', 'last_name', 'role', 'terms', 'newsletter'
        ]
    
    def validate_username(self, value):
        # Check username format
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', value):
            raise serializers.ValidationError(
                'Username must be 3-30 characters and contain only letters, numbers, and underscores.'
            )
        
        # Check if username already exists
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        
        return value
    
    def validate_email(self, value):
        # Check email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError('Please enter a valid email address.')
        
        # Check if email already exists
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        
        return value
    
    def validate_password(self, value):
        # Check password strength
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters long.')
        
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError('Password must contain at least one number.')
        
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError('Password must contain at least one uppercase letter.')
        
        if not any(char.islower() for char in value):
            raise serializers.ValidationError('Password must contain at least one lowercase letter.')
        
        return value
    
    def validate(self, attrs):
        # Check if passwords match
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        
        # Check if terms are accepted
        if not attrs.get('terms'):
            raise serializers.ValidationError({
                'terms': 'You must accept the terms and conditions.'
            })
        
        # Map role to user_type
        role_mapping = {
            'student': 'student',
            'researcher': 'researcher', 
            'activist': 'activist',
            'professional': 'professional'
        }
        
        role = attrs.get('role', 'student')
        attrs['user_type'] = role_mapping.get(role, 'public')
        
        return attrs
    
    def create(self, validated_data):
        # Remove extra fields before creating user
        validated_data.pop('confirm_password', None)
        validated_data.pop('terms', None)
        newsletter = validated_data.pop('newsletter', False)
        role = validated_data.pop('role', 'student')
        user_type = validated_data.pop('user_type', 'public')
        
        # Create the user
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=user_type,
            newsletter_subscription=newsletter
        )
        
        # Additional fields can be set here if needed
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'organization', 
                 'country', 'city', 'bio', 'profile_image', 'date_of_birth',
                 'phone_number', 'alternate_email', 'job_title', 'expertise',
                 'education', 'certifications', 'social_links', 'timezone',
                 'email_notifications', 'newsletter_subscription', 'language_preference']


class UserActivityLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserActivityLog
        fields = '__all__'


class UserVerificationSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    verified_by_username = serializers.CharField(source='verified_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = UserVerification
        fields = '__all__'


class UserStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    users_by_type = serializers.ListField()
    users_by_country = serializers.ListField()
    recent_signups = serializers.IntegerField()
    verification_stats = serializers.DictField()
    top_contributors = serializers.ListField()
    activity_last_24h = serializers.IntegerField()


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password".')
