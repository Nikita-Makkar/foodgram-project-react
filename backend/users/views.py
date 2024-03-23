from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from api.constants import (SUBSCRIPTION_ALREADY_EXISTS_ERROR,
                           SUBSCRIPTION_SELF_ERROR)
from api.paginations import CustomPagination
from api.permissions import IsOwnerOrReadOnly
from api.serializers import FollowSerializer
from recipes.models import Follow

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """ViewSet для модели пользователя
    """
    permission_classes = [IsOwnerOrReadOnly]
    pagination_class = CustomPagination

    @action(detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Просмотр подписок пользователя"""
        queryset = self.request.user.follower.all()
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(page,
                                      many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def create_subscription(self, request):
        """Создание подписки"""
        author_id = request.data.get('author_id')

        if author_id == request.user.id:
            return Response(SUBSCRIPTION_SELF_ERROR,
                            status=status.HTTP_400_BAD_REQUEST)

        if Follow.objects.filter(user=request.user,
                                 author_id=author_id
                                 ).exists():
            return Response(SUBSCRIPTION_ALREADY_EXISTS_ERROR,
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = FollowSerializer(
            data={'author': author_id, 'user': request.user.id})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(['get', 'put'], detail=False)
    def me(self, request, *args, **kwargs):
        """Получение профиля пользователя."""
        if request.user.is_authenticated:
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    @action(detail=True, methods=['get'],
            permission_classes=[AllowAny])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
