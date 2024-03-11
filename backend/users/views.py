from django.contrib.auth import get_user_model
from api.pagination import CustomPagination
from api.serializers import FollowSerializer
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from api.permissions import IsOwnerOrReadOnly

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """ViewSet пользователя
    """
    permission_classes = [IsOwnerOrReadOnly]
    pagination_class = CustomPagination
    

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Просмотр подписок пользователя"""
        queryset = self.request.user.follower.all()
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(page,
                                      many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)
