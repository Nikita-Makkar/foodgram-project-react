from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.constants import (AUTHENTION_ERROR, AUTHOR_NOT_FOUND_ERROR,
                           RECIPE_ALREADY_ADDED_ERROR,
                           RECIPE_ALREADY_ADDED_IN_CARD,
                           RECIPE_ALREADY_EXISTS_ERROR, RECIPE_NOT_FOUND_ERROR,
                           RECIPE_NOT_IN_FAVORITES_ERROR,
                           RECIPE_NOT_IN_SHOPPING_CART_ERROR,
                           SUBSCRIPTION_ALREADY_EXISTS_ERROR,
                           SUBSCRIPTION_NOT_FOUND_ERROR,
                           SUBSCRIPTION_SELF_ERROR)
from api.filters import IngredientFilter, RecipeFilter
from api.paginations import CustomPagination
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (FollowSerializer, IngredientSerializer,
                             RecipeFavoritesSerializer, RecipeSerializer,
                             ShoppingListSerializer, TagSerializer)
from recipes.models import (Follow, Ingredient, IngredientRecipes, Recipe,
                            RecipeFavorites, ShoppingList, Tag)
from users.models import CustomUser


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для модели Тег
    Получение списка тегов /
    конкретного тега
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
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
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed(AUTHENTION_ERROR)
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
        ingredients = IngredientRecipes.objects.filter(
            recipes__in=shopping_list_recipes
        ).values('ingredients__name',
                 'ingredients__measurement_unit'
                 ).annotate(
            total_amount=Sum('amount')
        )
        for ingredient in ingredients:
            name = ingredient['ingredients__name']
            measurement_unit = ingredient['ingredients__measurement_unit']
            total_amount = ingredient['total_amount']

            shopping_result[name] = {
                "measurement_unit": measurement_unit,
                "amount": total_amount,
            }

        shopping_itog = (
            f"{name} - {value['amount']} {value['measurement_unit']}\n"
            for name, value in shopping_result.items()
        )

        response = HttpResponse(shopping_itog, content_type="text/plain")
        response[
            'Content-Disposition'] = 'attachment; filename="shoppinglist.txt"'
        return response


class RecipeFavoritesViewSet(viewsets.ModelViewSet):
    """ViewSet для списка избранных рецептов
    Добавление /
    удаление из списка
    """
    serializer_class = RecipeFavoritesSerializer
    queryset = RecipeFavorites.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Добавление рецепта
        в список избранного
        """
        recipes_id = self.kwargs['id']
        try:
            recipes = Recipe.objects.get(id=recipes_id)
        except Recipe.DoesNotExist:
            raise ValidationError(RECIPE_NOT_FOUND_ERROR)
        recipes = get_object_or_404(Recipe, id=recipes_id)
        if not Recipe.objects.filter(id=recipes_id).exists():
            raise ValidationError(RECIPE_ALREADY_EXISTS_ERROR)
        if RecipeFavorites.objects.filter(user=request.user,
                                          recipes=recipes).exists():
            raise ValidationError(RECIPE_ALREADY_ADDED_ERROR)
        RecipeFavorites.objects.create(user=request.user, recipes=recipes)
        serializer = RecipeFavoritesSerializer()
        return Response(
            serializer.to_representation(instance=recipes),
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, *args, **kwargs):
        """Удаление рецепта из списка избранного"""
        recipe_id = self.kwargs['id']
        user_id = request.user.id
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            raise Http404(RECIPE_NOT_FOUND_ERROR)
        if not RecipeFavorites.objects.filter(user=request.user,
                                              recipes=recipe).exists():
            return Response(
                {RECIPE_NOT_IN_FAVORITES_ERROR},
                status=status.HTTP_400_BAD_REQUEST)
        RecipeFavorites.objects.filter(
            user__id=user_id,
            recipes__id=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
            raise ValidationError(SUBSCRIPTION_SELF_ERROR)
        if Follow.objects.filter(user=request.user, author=user).exists():
            return Response(
                {SUBSCRIPTION_ALREADY_EXISTS_ERROR},
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
                {SUBSCRIPTION_NOT_FOUND_ERROR},
                status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingViewSet(viewsets.ModelViewSet):
    """ViewSet для списока покупок
    Добавление рецепта в список покупок /
    удаление рецепта из списка покупок /
    скачивание списка покупок
    """
    serializer_class = ShoppingListSerializer
    pagination_class = CustomPagination
    queryset = ShoppingList.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Добавление рецепта в
        список покупок
        """
        recipe_id = self.kwargs['id']
        try:
            recipes = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            raise ValidationError(RECIPE_NOT_FOUND_ERROR)
        if ShoppingList.objects.filter(user=request.user,
                                       recipes=recipes).exists():
            return Response({RECIPE_ALREADY_ADDED_IN_CARD},
                            status=status.HTTP_400_BAD_REQUEST)

        ShoppingList.objects.create(user=request.user, recipes=recipes)
        serializer = ShoppingListSerializer()
        return Response(
            serializer.to_representation(instance=recipes),
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, *args, **kwargs):
        """Удаление рецепта из
        списка покупок
        """
        recipe_id = self.kwargs['id']
        user_id = request.user.id
        try:
            Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            raise Http404(RECIPE_NOT_FOUND_ERROR)

        if not ShoppingList.objects.filter(user__id=user_id,
                                           recipes__id=recipe_id).exists():
            return Response({RECIPE_NOT_IN_SHOPPING_CART_ERROR},
                            status=status.HTTP_400_BAD_REQUEST)
        ShoppingList.objects.filter(user__id=user_id,
                                    recipes__id=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
