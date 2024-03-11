from django.contrib import admin
from django.contrib import admin

from .models import (RecipeFavorites, Ingredient, Recipe, IngredientRecipes,
                     ShoppingList, Tag)


class RecipeIngredientInline(admin.TabularInline):
    model = IngredientRecipes
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'author', 'favorites_count')
    search_fields = ('name',)
    list_filter = ('name', 'author', 'tags')
    exclude = ('ingredients',)

    def favorites_count(self, obj):
        return obj.favorites.count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(RecipeFavorites)
admin.site.register(ShoppingList)