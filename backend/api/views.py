from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from djoser.views import UserViewSet

from api.constants import (AUTHOR_NOT_FOUND_ERROR,
                           RECIPE_ALREADY_ADDED_ERROR,
                           RECIPE_ALREADY_ADDED_IN_CARD,
                           RECIPE_NOT_IN_FAVORITES_ERROR,
                           RECIPE_NOT_IN_SHOPPING_CART_ERROR,
                           SUBSCRIPTION_ALREADY_EXISTS_ERROR,
                           SUBSCRIPTION_NOT_FOUND_ERROR,
                           SUBSCRIPTION_SELF_ERROR)
from api.mixins import RecipeActionMixin
from api.filters import IngredientFilter, RecipeFilter
from api.paginations import CustomPagination
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (FollowSerializer, IngredientSerializer,
                             FavoriteRecipeSerializer, RecipeSerializer,
                             ShoppingListSerializer, TagSerializer)
from recipes.models import (Follow, Ingredient, IngredientRecipe, Recipe,
                            FavoriteRecipe, ShoppingList, Tag)
from users.models import CustomUser


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

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(['get', 'put'], detail=False,
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        """Получение профиля пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для модели Тег
    Получение списка тегов /
    конкретного тега
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для модели Ингредиенты
    Получение списка ингредиентов /
    конкретного ингредиента
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet Рецепт
    Получение списка рецептов /
    конкретного рецепта /
    создание, редактирование /
    удаление рецепта
    """
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['GET'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачивание списка покупок для выбранных
        рецептов данные суммируются.
        """
        shopping_result = {}
        shopping_list_recipes = Recipe.objects.filter(
            shoppingcart__user=request.user)
        ingredients = IngredientRecipe.objects.filter(
            recipe__in=shopping_list_recipes
        ).values('ingredient__name',
                 'ingredient__measurement_unit'
                 ).annotate(
            total_amount=Sum('amount')
        )
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            total_amount = ingredient['total_amount']

            shopping_result[name] = {
                "measurement_unit": measurement_unit,
                "amount": total_amount,
            }

        response = HttpResponse((
            f"{name} - {value['amount']} {value['measurement_unit']}\n"
            for name, value in shopping_result.items()
        ), content_type="text/plain")
        response[
            'Content-Disposition'] = 'attachment; filename="shoppinglist.txt"'
        return response


class FollowViewSet(viewsets.ModelViewSet):
    """ViewSet для подписки
    Cоздание подписки /
    удаление подписки
    """
    serializer_class = FollowSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Создание подписки"""
        user_id = self.kwargs['id']
        user = get_object_or_404(CustomUser, id=user_id)

        if user == request.user:
            return Response(SUBSCRIPTION_SELF_ERROR,
                            status=status.HTTP_400_BAD_REQUEST)
        if Follow.objects.filter(user=request.user, author=user).exists():
            return Response(
                SUBSCRIPTION_ALREADY_EXISTS_ERROR,
                status=status.HTTP_400_BAD_REQUEST)

        subscribe = Follow.objects.create(user=request.user, author=user)

        serializer = FollowSerializer(subscribe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """Удаление подписки"""
        author_id = self.kwargs['id']
        user_id = request.user.id
        try:
            CustomUser.objects.get(id=author_id)
        except CustomUser.DoesNotExist:
            raise Http404(AUTHOR_NOT_FOUND_ERROR)
        try:
            subscription = Follow.objects.get(
                user_id=user_id,
                author_id=author_id)
        except Follow.DoesNotExist:
            return Response(
                SUBSCRIPTION_NOT_FOUND_ERROR,
                status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteRecipeViewSet(RecipeActionMixin, viewsets.ModelViewSet):
    """ViewSet для списка избранных рецептов
    Добавление /
    удаление из списка
    """
    serializer_class = FavoriteRecipeSerializer
    queryset = FavoriteRecipe.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Добавление рецепта в список избранного"""
        recipe_id = self.kwargs['id']
        return self.add_recipe_to_list(
            request,
            recipe_id,
            FavoriteRecipe,
            RECIPE_ALREADY_ADDED_ERROR)

    def delete(self, request, *args, **kwargs):
        """Удаление рецепта из списка избранного"""
        recipe_id = self.kwargs['id']
        return self.remove_recipe_from_list(
            request,
            recipe_id,
            FavoriteRecipe,
            RECIPE_NOT_IN_FAVORITES_ERROR)


class ShoppingViewSet(RecipeActionMixin, viewsets.ModelViewSet):
    """ViewSet для списка покупок
    Добавление рецепта в список покупок /
    удаление рецепта из списка покупок /
    скачивание списка покупок
    """
    serializer_class = ShoppingListSerializer
    pagination_class = CustomPagination
    queryset = ShoppingList.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Добавление рецепта в список покупок"""
        recipe_id = self.kwargs['id']
        return self.add_recipe_to_list(
            request,
            recipe_id,
            ShoppingList,
            RECIPE_ALREADY_ADDED_IN_CARD)

    def delete(self, request, *args, **kwargs):
        """Удаление рецепта из списка покупок"""
        recipe_id = self.kwargs['id']
        return self.remove_recipe_from_list(
            request,
            recipe_id,
            ShoppingList,
            RECIPE_NOT_IN_SHOPPING_CART_ERROR)
