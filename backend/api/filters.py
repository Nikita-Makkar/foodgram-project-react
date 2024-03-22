from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтрация по избранному, автору, списку покупок и тегам."""

    author = filters.ModelChoiceFilter(
        field_name='author',
        label='Автор',
        queryset=User.objects.all(),
    )

    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        label='Тэги',
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
        label='Избранные рецепты',)
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart', label='В списке покупок',
    )

    class Meta:
        model = Recipe
        fields = ['author',
                  'tags',
                  'is_favorited',
                  'is_in_shopping_cart', ]

    def filter_is_favorited(self, queryset, name, value):
        if (value and self.request.user
            and not isinstance(
                self.request.user, AnonymousUser)):
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if (value and self.request.user and not isinstance(
                self.request.user, AnonymousUser)):
            return queryset.filter(shoppingcart__user=self.request.user)
        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтрация ингредиентов по названию."""

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
