from rest_framework.response import Response
from rest_framework import status

from api.constants import RECIPE_NOT_FOUND_ERROR
from recipes.models import Recipe


class RecipeActionMixin:
    def get_recipe(self, recipe_id):
        try:
            return Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return None

    def add_recipe_to_list(self,
                           request,
                           recipe_id,
                           list_model,
                           error_response):
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return Response(RECIPE_NOT_FOUND_ERROR,
                            status=status.HTTP_400_BAD_REQUEST)

        if list_model.objects.filter(user=request.user,
                                     recipe=recipe).exists():
            return Response(error_response,
                            status=status.HTTP_400_BAD_REQUEST)
        list_model.objects.create(user=request.user, recipe=recipe)
        serializer = self.get_serializer()
        return Response(
            serializer.to_representation(instance=recipe),
            status=status.HTTP_201_CREATED)

    def remove_recipe_from_list(self,
                                request,
                                recipe_id,
                                list_model,
                                error_response):
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return Response(RECIPE_NOT_FOUND_ERROR,
                            status=status.HTTP_404_NOT_FOUND)

        user_id = request.user.id
        if not list_model.objects.filter(user__id=user_id,
                                         recipe__id=recipe_id).exists():
            return Response(error_response,
                            status=status.HTTP_400_BAD_REQUEST)
        list_model.objects.filter(
            user__id=user_id,
            recipe__id=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
