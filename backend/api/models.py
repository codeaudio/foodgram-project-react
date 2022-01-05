from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CASCADE, UniqueConstraint


class CustomUser(AbstractUser):
    username = models.CharField(
        unique=True,
        verbose_name='username',
        max_length=30
    )
    email = models.EmailField(
        unique=True,
        verbose_name='адрес почты'
    )
    first_name = models.CharField(
        null=False,
        max_length=150,
        blank=False,
        verbose_name='Информация',
    )
    last_name = models.CharField(
        null=False,
        max_length=35,
        blank=False,
        verbose_name='Имя пользователя',
    )
    password = models.CharField(
        null=False,
        max_length=90,
        blank=False,
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
        null=False,
        max_length=200,
        blank=False,
        verbose_name='название тега',
    )
    color = models.CharField(
        null=True,
        max_length=7,
        verbose_name='цвет в HEX',
    )
    slug = models.CharField(
        null=True,
        max_length=200,
        verbose_name='Уникальный слаг'
    )

    class Meta:
        db_table = 'tag'


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        db_table = 'ingredient'


class Recipe(models.Model):
    ingredients = models.ManyToManyField(Ingredient, related_name='recipes', through='RecipeIngredient', blank=False)
    tags = models.ManyToManyField(Tag, related_name='recipes', through='RecipeTag')
    name = models.CharField(max_length=200)
    text = models.TextField()
    image = models.ImageField()
    cooking_time = models.IntegerField()
    author = models.ForeignKey(CustomUser, on_delete=CASCADE)

    class Meta:
        db_table = 'recipe'
        ordering = ['-id']


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='reciperecipeingredients', on_delete=CASCADE)
    ingredient = models.ForeignKey(Ingredient, related_name='ingridientsrecipeingredients', on_delete=CASCADE)
    amount = models.IntegerField(null=False)

    class Meta:
        db_table = 'recipe_ingredient'
        constraints = [
            UniqueConstraint(fields=['recipe', 'ingredient'], name='recipe_ingredient_uniq')
        ]


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=CASCADE)
    tag = models.ForeignKey(Tag, on_delete=CASCADE)

    class Meta:
        db_table = 'recipe_tag'
        constraints = [
            UniqueConstraint(fields=['recipe', 'tag'], name='recipe_tag_uniq')
        ]


class RecipeFavorite(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=CASCADE, related_name='favorites')
    user = models.ForeignKey(CustomUser, on_delete=CASCADE, related_name='favorited')
    recipe = models.ForeignKey(Recipe, on_delete=CASCADE, related_name='recipefavorite')

    class Meta:
        db_table = 'recipe_favorite'
        constraints = [
            UniqueConstraint(fields=['author', 'user', 'recipe'], name='favorite_uniq')
        ]


class Subscribe(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=CASCADE, related_name='subscribe')
    user = models.ForeignKey(CustomUser, on_delete=CASCADE, related_name='subscribed')

    class Meta:
        db_table = 'subscribe'
        constraints = [
            UniqueConstraint(fields=['author', 'user'], name='subscribe_uniq')
        ]


class ShoppingList(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=CASCADE, related_name='shopper')
    recipe = models.ForeignKey(Recipe, on_delete=CASCADE, related_name='shopped')

    class Meta:
        db_table = 'shopping_list'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'], name='shop_uniq')
        ]
