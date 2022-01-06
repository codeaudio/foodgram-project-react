import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import validate_email
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, Tag, Recipe, Ingredient, RecipeIngredient, RecipeFavorite, Subscribe, ShoppingList


class CustomSerializer(serializers.TokenObtainPairSerializer, ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'password')

    def validate(self, data):
        user_data = dict(data)
        email = user_data.get('email')
        validate_email(email)
        password = user_data.get('password')
        user = get_object_or_404(
            CustomUser,
            email=email
        )
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return {
                'auth_token': str(refresh.access_token)
            }
        return Response({'auth_token': 'null'}, status=status.HTTP_401_UNAUTHORIZED)


class ProfileSerializer(ModelSerializer):
    is_subscribed = serializers.serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        return Subscribe.objects.filter(
            user=self.context['request'].user.id, author=obj.id
        ).exists()


class ProfileCreateSerializer(ModelSerializer):
    is_subscribed = serializers.serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name')


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(ModelSerializer):
    class Meta:
        model = RecipeIngredient
        fields = '__all__'


class RecipeIngredientSerializer(ModelSerializer):
    id = serializers.serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipePostOrUpdateSerializer(ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.serializers.ListField(required=True)
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'text', 'name', 'cooking_time', 'image', 'author')

    def validate_empty_values(self, data):
        return True, data

    def get_is_subscribed(self, obj):
        return Subscribe.objects.filter(
            user=self.context['request'].user.id, author=obj.author.id
        ).exists()


class RecipeUpdateSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'text', 'name', 'cooking_time', 'image')

    def validate_empty_values(self, data):
        return True, data


class RelatedIngredientRecipeUpdateSerializer(ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('ingredients',)


class RelatedTagRecipeUpdateSerializer(ModelSerializer):
    tags = serializers.serializers.ListField(required=True)

    class Meta:
        model = Recipe
        fields = ('tags',)


class RelatedIngredientRecipeSerializer(ModelSerializer):
    id = serializers.serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeGetSerializer(ModelSerializer):
    ingredients = RelatedIngredientRecipeSerializer(
        source='reciperecipeingredients', many=True
    )
    tags = TagSerializer(many=True, read_only=True)
    author = ProfileSerializer(read_only=True)
    is_favorited = serializers.serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'text', 'name',
                  'cooking_time', 'author', 'image', 'is_favorited',
                  'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        return RecipeFavorite.objects.filter(
            user=self.context['request'].user.id, recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingList.objects.filter(
            user=self.context['request'].user.id, recipe=obj.id
        ).exists()


class RecipeFavoriteSerializer(ModelSerializer):
    class Meta:
        model = RecipeFavorite
        fields = '__all__'


class SubscribeSerializer(ModelSerializer):
    class Meta:
        model = Subscribe
        fields = '__all__'


class RelatedUserSubscribeGetSerializer(ModelSerializer):
    id = serializers.serializers.ReadOnlyField(source='author.id')
    email = serializers.serializers.ReadOnlyField(source='author.email')
    username = serializers.serializers.ReadOnlyField(source='ingredient.username')
    first_name = serializers.serializers.ReadOnlyField(source='ingredient.first_name')
    last_name = serializers.serializers.ReadOnlyField(source='ingredient.last_name')

    class Meta:
        model = CustomUser
        fields = ("id", "email", "username", "first_name", "last_name")


class RelatedRecipeSubscribeGetSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'


class SubscribeGetSerializer(ModelSerializer):
    id = serializers.serializers.ReadOnlyField(source='author.id')
    email = serializers.serializers.ReadOnlyField(source='author.email')
    username = serializers.serializers.ReadOnlyField(source='author.username')
    first_name = serializers.serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.serializers.SerializerMethodField()
    recipes = serializers.serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        exclude = ('user', 'author')

    def get_recipes(self, obj):
        queryset = Recipe.objects.filter(author__in=list(
            Subscribe.objects.filter(
                user=self.context['request'].user.id, author=obj.author
            ).values_list('author',flat=True))
        ).values('id', 'name', 'image', 'cooking_time')[:int(self.context['request'].query_params.get('recipes_limit'))]
        serialized = json.dumps(list(queryset),cls=DjangoJSONEncoder)
        result = json.loads(serialized)
        for i in result:
            for k, v in i.items():
                if k == 'image':
                    image = i['image']
                    i['image'] = self.context['request'].META.get('wsgi.url_scheme') + '://' + self.context[
                        'request'].get_host() + '/mediadjango/' + image
        return result

    def get_is_subscribed(self, obj):
        return Subscribe.objects.filter(
            user=self.context['request'].user.id, author=obj.author
        ).exists()


class ShoppingListGetSerializer(ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')
