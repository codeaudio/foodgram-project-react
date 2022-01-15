from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CASCADE, UniqueConstraint


class CustomUser(AbstractUser):
    username = models.CharField(
        unique=True,
        max_length=30,
        verbose_name='username'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='адрес почты'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Информация',
    )
    last_name = models.CharField(
        max_length=35,
        verbose_name='Имя пользователя',
    )
    password = models.CharField(
        max_length=90,
        verbose_name='Пароль пользователя',
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'password', 'first_name', 'last_name')

    class Meta:
        db_table = 'user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-id']

    def __str__(self):
        return self.email


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='название тега',
    )
    color = models.CharField(
        null=True,
        max_length=7,
        verbose_name='цвет в HEX',
    )
    slug = models.CharField(
        unique=True,
        null=True,
        max_length=200,
        verbose_name='Уникальный слаг'
    )

    class Meta:
        db_table = 'tag'
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='наименование'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Вес'
    )

    class Meta:
        db_table = 'ingredient'
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='RecipeIngredient',
        verbose_name='Ингредиенты рецепта'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        through='RecipeTag',
        verbose_name='Теги рецепта'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Наименование'
    )
    text = models.TextField(verbose_name='Текст')
    image = models.ImageField(verbose_name='Изображение')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',

    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )

    class Meta:
        db_table = 'recipe'
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        on_delete=CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='recipe_ingredients',
        on_delete=CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(
        verbose_name='Кол-во'
    )

    class Meta:
        db_table = 'recipe_ingredient'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'], name='recipe_ingredient_uniq'
            )
        ]
        verbose_name = 'Ингрединт рецепта'
        verbose_name_plural = 'Ингрединты рецепта'

    def __str__(self):
        return str(self.id)


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=CASCADE,
        related_name='recipe_tag',
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=CASCADE,
        related_name='recipe_tag',
        verbose_name='Тег'
    )

    class Meta:
        db_table = 'recipe_tag'
        constraints = [
            UniqueConstraint(fields=['recipe', 'tag'], name='recipe_tag_uniq')
        ]
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'

    def __str__(self):
        return str(self.id)


class RecipeFavorite(models.Model):
    author = models.ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='favorites',
        verbose_name='Автор'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='favorited',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=CASCADE,
        related_name='recipe_favorite',
        verbose_name='Рецепт'
    )

    class Meta:
        db_table = 'recipe_favorite'
        constraints = [
            UniqueConstraint(
                fields=['author', 'user', 'recipe'], name='favorite_uniq'
            )
        ]
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'

    def __str__(self):
        return str(self.id)


class Subscribe(models.Model):
    author = models.ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='subscribe',
        verbose_name='Автор'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='subscribed',
        verbose_name='Пользователь'
    )

    class Meta:
        db_table = 'subscribe'
        constraints = [
            UniqueConstraint(fields=['author', 'user'], name='subscribe_uniq')
        ]
        verbose_name = 'Подсписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return str(self.id)


class ShoppingList(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='shopper',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=CASCADE,
        related_name='shopped',
        verbose_name='Рецепт'
    )

    class Meta:
        db_table = 'shopping_list'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'], name='shop_uniq')
        ]
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'

    def __str__(self):
        return str(self.id)
