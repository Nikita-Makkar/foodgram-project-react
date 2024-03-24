from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.validators import UniqueValidator

from api.constants import (IMAGE_NOT_IN_RECIPE, INGREDIENT_ALREADY_ADDED,
                           INGREDIENT_AMOUNT_FORMAT_ERROR,
                           INGREDIENT_WITH_THIS_ID_NOT_EXISTS,
                           INGREDIENTS_NOT_IN_RECIPE, NOT_ID_INGREDIENTS,
                           SUBSCRIPTION_ALREADY_EXISTS_ERROR,
                           SUBSCRIPTION_SELF_ERROR, TAG_ALREADY_ADDED,
                           TAG_WITH_THIS_ID_NOT_EXISTS, TAGS_NOT_IN_RECIPE,
                           INVALID_CHARTERS_IN_USRNAME)
from recipes.models import (Follow, Ingredient, IngredientRecipe, Recipe,
                            FavoriteRecipe, ShoppingList, Tag)


User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор для получения списка
    пользователей и определенного пользователя"""
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователя"""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Создание пользователя"""
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())])
    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=INVALID_CHARTERS_IN_USRNAME
            )
        ]
    )

    def create(self, validated_data):
        """Создаёт нового пользователя с запрошенными полями.
        """
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'password',
                  'username',
                  'first_name',
                  'last_name')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'password': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор Теги"""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор Ингредиенты"""
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор Ингредиенты в рецепте"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = IngredientRecipe
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор Рецепт"""
    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientRecipeSerializer(
        many=True, source='ingredientrecipe_set', read_only=True
    )
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        ]

    def get_is_favorited(self, obj):
        """Проверка наличия рецепта в избранном"""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(
            recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка наличия рецепта в списке покупок"""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.shoppingcart.filter(user=user).exists()

    def validate_ingredients(self, ingredients):
        """Валидация ингредиентов"""
        ingredients_result = []
        ingredient_ids = set()

        for ingredient_item in ingredients:
            ingredient_id = ingredient_item.get('id')
            amount = ingredient_item.get('amount')

            if not ingredient_id:
                raise serializers.ValidationError(NOT_ID_INGREDIENTS)
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(INGREDIENT_ALREADY_ADDED)
            ingredient_ids.add(ingredient_id)

            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    INGREDIENT_WITH_THIS_ID_NOT_EXISTS)
            if not (
                isinstance(ingredient_item['amount'], int)
                or ingredient_item['amount'].isdigit()
            ):
                raise serializers.ValidationError(
                    INGREDIENT_AMOUNT_FORMAT_ERROR)
            ingredients_result.append(
                {'ingredients': ingredient,
                 'amount': amount})
        return ingredients_result

    def validate_tags(self, tags_data):
        """Валидация тегов"""
        tag_list = []
        for tag_id in tags_data:
            if tag_id in tag_list:
                raise serializers.ValidationError(TAG_ALREADY_ADDED)
            try:
                Tag.objects.get(id=tag_id)
            except Tag.DoesNotExist:
                raise serializers.ValidationError(TAG_WITH_THIS_ID_NOT_EXISTS)
            tag_list.append(tag_id)

        return tag_list

    def validate(self, data):
        """Метод для валидации данных перед созданием рецепта"""
        ingredients = self.initial_data.get('ingredients')
        tags_data = self.initial_data.get('tags')
        image = self.initial_data.get('image')

        if not ingredients:
            raise serializers.ValidationError(INGREDIENTS_NOT_IN_RECIPE)
        if not tags_data:
            raise serializers.ValidationError(TAGS_NOT_IN_RECIPE)
        if not image:
            raise serializers.ValidationError(IMAGE_NOT_IN_RECIPE)

        data['ingredients'] = self.validate_ingredients(ingredients)
        data['tags'] = self.validate_tags(tags_data)

        return data

    def create_ingredients(self, ingredients, recipe):
        """Добавление ингредиентов"""
        return IngredientRecipe.objects.bulk_create([
            IngredientRecipe(
                recipe=recipe,
                ingredient=ingredient['ingredients'],
                amount=ingredient.get('amount'),
            ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        """Создание рецепта"""
        image = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(image=image, **validated_data)
        self.create_ingredients(ingredients_data, recipe)
        tags = Tag.objects.filter(id__in=tags_data)
        recipe.tags.add(*tags)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта"""
        instance.tags.clear()
        tags_data = validated_data.pop('tags', [])
        instance.tags.set(tags_data)
        ingredients_data = validated_data.pop('ingredients', [])
        self.create_ingredients(ingredients_data, instance)
        return super().update(instance, validated_data)


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор Списки избранных рецептов"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField(
        max_length=None,
        use_url=False,
    )
    cooking_time = serializers.IntegerField()

    class Meta:
        model = FavoriteRecipe
        fields = ['id', 'name', 'image', 'cooking_time']
        validators = UniqueTogetherValidator(
            queryset=FavoriteRecipe.objects.all(), fields=('user', 'recipes')
        )


class FollowRecipeSerializer(serializers.ModelSerializer):
    """Урезанный сериализатор Рецепты для сериализатора Подписки ниже"""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']
        read_only_fields = ['id', 'name', 'image', 'cooking_time']


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор Подписки"""
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        ]

    def validate(self, data):
        """Валидация подписки.
        """
        user = self.context.get('request').user
        author = data['author']

        if user == author:
            raise serializers.ValidationError(SUBSCRIPTION_SELF_ERROR)

        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                SUBSCRIPTION_ALREADY_EXISTS_ERROR)
        return data

    def get_is_subscribed(self, obj):
        """Проверка подписки
        текущего пользователя на автора
        """
        return Follow.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        """Получение рецептов автора"""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[: int(limit)]
        return FollowRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        """Получение общего
        количества рецептов автора
        """
        return Recipe.objects.filter(author=obj.author).count()


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор Список покупок"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField(max_length=None, use_url=False)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = ShoppingList
        fields = ['id', 'name', 'image', 'cooking_time']
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(), fields=('user', 'recipes')
            )
        ]
