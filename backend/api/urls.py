from django.urls import include, path, re_path
from rest_framework import routers

from api.views import (FollowViewSet, IngredientsViewSet,
                       RecipeFavoritesViewSet, RecipeViewSet, ShoppingViewSet,
                       TagViewSet)
from users.views import CustomUserViewSet

app_name = 'api'

router = routers.DefaultRouter()

router.register('tags', TagViewSet)
router.register('users', CustomUserViewSet)
router.register('ingredients', IngredientsViewSet)
router.register('recipes', RecipeViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('', include("djoser.urls")),
    re_path('auth/', include('djoser.urls.authtoken')),
    path('recipes/<int:id>/favorite/',
         RecipeFavoritesViewSet.as_view(
              {'post': 'create', 'delete': 'delete'}),
         name='favorite',
         ),

    path('users/<int:id>/subscribe/',
         FollowViewSet.as_view({'post': 'create', 'delete': 'delete'}),
         name='subscribe',
         ),

    path('recipes/<int:id>/shopping_cart/',
         ShoppingViewSet.as_view({'post': 'create', 'delete': 'delete'}),
         name='shopping_cart',
         ),
]
