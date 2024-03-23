from django.contrib import admin

from .models import (Ingredient, IngredientRecipe, Recipe, FavoriteRecipe,
                     ShoppingList, Tag)


class RecipeIngredientInline(admin.TabularInline):
    """
    Админ-зона для интеграции добавления ингридиентов в рецепты.
    """
    model = IngredientRecipe
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    """Админ-зона рецептов.
    Добавлен просмотр кол-ва добавленных рецептов в избранное.
    """
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'author', 'favorites_count')
    search_fields = ('name',)
    list_filter = ('name', 'author', 'tags')
    exclude = ('ingredients',)

    def favorites_count(self, obj):
        return obj.favorite.count()

    favorites_count.short_description = 'Количество добавлений в избранное'


class IngredientAdmin(admin.ModelAdmin):
    """
    Админзона ингридиентов.
    """
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    """
    Админзона тегов.
    """
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(FavoriteRecipe)
admin.site.register(ShoppingList)
