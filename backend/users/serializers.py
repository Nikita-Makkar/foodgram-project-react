from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import Follow
from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField
from django.core.validators import RegexValidator

from rest_framework.validators import UniqueValidator

from django.contrib.auth import get_user_model


User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор для получения списка
    пользователей и определенного пользователя"""
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
    def get_is_subscribed(self, obj):
        """Проверка подписки пользователя"""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Создание пользователя"""
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())])
    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Username can only contain letters, digits, and @/./+/-/_ characters.'
            )
        ]
    )

    def create(self, validated_data: dict) -> User:
        """Создаёт нового пользователя с запрошенными полями.
        """
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'password',
                  'username',
                  'first_name',
                  'last_name')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'password': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }