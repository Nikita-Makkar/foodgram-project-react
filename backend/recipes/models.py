from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Exists, OuterRef
from django.core.validators import MinValueValidator
from django.core import validators


User = get_user_model()


class Tag(models.Model):
    """Тэги."""
    BLUE = '#0000FF'
    ORANGE = '#FFA500'
    GREEN = '#008000'
    PURPLE = '#800080'
    YELLOW = '#FFFF00'

    COLOR_CHOICES = [
        (BLUE, 'Синий'),
        (ORANGE, 'Оранжевый'),
        (GREEN, 'Зеленый'),
        (PURPLE, 'Фиолетовый'),
        (YELLOW, 'Желтый'),
    ]
    color = models.CharField(max_length=7, unique=True, choices=COLOR_CHOICES,
                             verbose_name='Цвет в HEX')
    name = models.CharField(
        max_length=200, verbose_name='Название тега', unique=True
    )
    slug = models.SlugField(
        max_length=200, null=True, verbose_name='Слаг', unique=True
    )
    id = models.AutoField(primary_key=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['-id']

    def __str__(self):
        return f' {self.name} {self.slug}'


class Ingredient(models.Model):
    """Ингредиенты"""
    name = models.CharField(max_length=200,
                            verbose_name='Название ингридиента')
    measurement_unit = models.CharField(
        max_length=200, verbose_name='Единицы измерения'
    )
    id = models.AutoField(primary_key=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'], name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class IngredientRecipes(models.Model):
    amount = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(
                1, message='Минимальное количество ингридиентов 1'),),
        verbose_name='Количество',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    def __str__(self):
        return f'{self.ingredient} в {self.recipe}'

    class Meta:
        ordering = ['-id']
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='unique_ingredients_recipe')
        ]



class RecipeFavorites(models.Model):
    """Модель Избранные рецепты"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь',
                             )

    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE,
                               related_name='favorites',
                               verbose_name='Рецепт')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe_for_user'),
        ]

    def __str__(self):
        return f'Список избранных рецептов{self.user} - {self.recipe}'


class RecipeQuerySet(models.QuerySet):
    def add_user_annotations(self, user_id: Optional[int]):
        return self.annotate(
            is_favorite=Exists(
                RecipeFavorites.objects.filter(
                    user_id=user_id,
                    recipe_id=OuterRef('pk'))
            ),
            is_in_shoppingcart=Exists(
                ShoppingList.objects.filter(
                    user_id=user_id,
                    recipe_id=OuterRef('pk'))
            ),
        )


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes',
    )
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта')
    text = models.TextField(verbose_name='Описание рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        through=IngredientRecipes,
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты'
    )

    #ingredients = models.ManyToManyField(
    #    Ingredient,
    #    through='RecipesIngredient',
    #    verbose_name='Ингредиенты',
    #    related_name='recipes',
    #)
    cooking_time = models.PositiveIntegerField(
        'Время приготовления в мин',
        validators=[
            MinValueValidator(1, 'Время приготовления не может '
                                 'быть меньше 1 минуты')
        ],
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
        blank=True
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shoppingcart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoppingcart',
        verbose_name='Рецепт',
    )
    id = models.AutoField(primary_key=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shoppingcart_user')
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Follow(models.Model):
    """Модель Подписки"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Отслеживаемый автор'
    )

    class Meta:
        ordering = ['-id']
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_following'
            ),
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан {self.author}'
