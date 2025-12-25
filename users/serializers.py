# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import CustomUser, UserActivityLog, UserVerification


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
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 
                 'user_type', 'organization', 'country', 'city', 'date_of_birth',
                 'phone_number', 'bio']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=validated_data.get('user_type', 'public'),
            organization=validated_data.get('organization', ''),
            country=validated_data.get('country', ''),
            city=validated_data.get('city', ''),
            date_of_birth=validated_data.get('date_of_birth'),
            phone_number=validated_data.get('phone_number', ''),
            bio=validated_data.get('bio', '')
        )
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