from django.contrib.auth import get_user_model
from django.core import validators
from django.core.validators import MinValueValidator
from django.db import models

from api.constants import COOKING_TIME_ERROR, INGREDIENT_AMOUNT_ERROR


User = get_user_model()


class Tag(models.Model):
    """Тэги."""
    RED = '#FF0000'
    ORANGE = '#FFA500'
    YELLOW = '#FFFF00'
    GREEN = '#008000'
    BLUE = '#0000FF'
    PURPLE = '#800080'

    COLOR_CHOICES = [
        (RED, 'Красный'),
        (ORANGE, 'Оранжевый'),
        (YELLOW, 'Желтый'),
        (GREEN, 'Зеленый'),
        (BLUE, 'Синий'),
        (PURPLE, 'Фиолетовый'),
    ]
    id = models.AutoField(primary_key=True)
    color = models.CharField(max_length=7, unique=True, choices=COLOR_CHOICES,
                             verbose_name='Цвет в HEX')
    name = models.CharField(
        max_length=200, verbose_name='Название тега', unique=True
    )
    slug = models.SlugField(
        max_length=200, null=True, verbose_name='Слаг', unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['-id']

    def __str__(self):
        return f' {self.name} {self.slug}'


class Ingredient(models.Model):
    """Ингредиенты"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200,
                            verbose_name='Название ингридиента')
    measurement_unit = models.CharField(
        max_length=200, verbose_name='Единицы измерения'
    )

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


class Recipe(models.Model):
    """Модель Рецептов"""
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта')
    text = models.TextField(verbose_name='Описание рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipes',
        verbose_name='Ингредиенты',
        related_name='recipes',
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления в мин',
        validators=[
            MinValueValidator(1, COOKING_TIME_ERROR)
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

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipes(models.Model):
    """Модель для связи рецепта и ингредиентов"""
    amount = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(
                1, message=INGREDIENT_AMOUNT_ERROR),),
        verbose_name='Количество',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    def __str__(self):
        return f'{self.ingredients} в {self.recipes}'

    class Meta:
        ordering = ['-id']
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(fields=['ingredients', 'recipes'],
                                    name='unique_ingredients_recipes')
        ]


class RecipeFavorites(models.Model):
    """Модель Избранные рецепты"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь',
                             )

    recipes = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipes'],
                name='unique_favorite_recipe_for_user'),
        ]

    def __str__(self):
        return f'Список избранных рецептов{self.user} - {self.recipes}'


class ShoppingList(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shoppingcart',
        verbose_name='Пользователь',
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoppingcart',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipes'],
                                    name='unique_shoppingcart_user')
        ]

    def __str__(self):
        return f'{self.user} - {self.recipes}'


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
