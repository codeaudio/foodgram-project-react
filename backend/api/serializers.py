from django.core.validators import validate_email
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, Tag, Recipe, Ingredient, RecipeIngredient


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
    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name', 'last_name')


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
    id = serializers.serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipePostOrUpdateSerializer(ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.serializers.ListField(required=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'text', 'name', 'cooking_time', 'image')

    def validate_empty_values(self, data):
        return True, data


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
    measurement_unit = serializers.serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeGetSerializer(ModelSerializer):
    ingredients = RelatedIngredientRecipeSerializer(source='recipeingredients', many=True)
    tags = TagSerializer(many=True, read_only=True)
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'text', 'name', 'cooking_time', 'author', 'image')
        depth = 1
