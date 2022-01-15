import asyncio

from asgiref.sync import sync_to_async
from django.core.validators import validate_email
from djoser.serializers import UserCreateSerializer
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_simplejwt import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .custom_serializer_field import Base64ImageField
from .exception import CustomApiException
from .models import (CustomUser, Tag, Recipe, Ingredient,
                     RecipeIngredient, RecipeFavorite, Subscribe,
                     ShoppingList, RecipeTag)


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
        raise CustomApiException(
            detail={'auth_token': 'null'},
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ProfileSerializer(ModelSerializer):
    is_subscribed = serializers.serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        return Subscribe.objects.filter(
            user=self.context['request'].user.id, author=obj.id
        ).exists()


class ProfileCreateSerializer(UserCreateSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'password')


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
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True
    )
    image = Base64ImageField(use_url=True)
    tags = serializers.serializers.ListField()
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'text', 'name',
                  'cooking_time', 'image', 'author')

    def get_is_subscribed(self, obj):
        return Subscribe.objects.filter(
            user=self.context['request'].user.id, author=obj.author.id
        ).exists()

    def create(self, validated_data):
        ingredients = validated_data.get('recipe_ingredients')
        tags = validated_data.get('tags')
        recipe_instance = Recipe(
            text=validated_data.get('text'),
            name=validated_data.get('name'),
            cooking_time=validated_data.get('cooking_time'),
            author=self.context['request'].user,
            image=validated_data.get('image')
        )
        recipe_instance.save()

        @sync_to_async
        def create_ing():
            for ingredient in ingredients:
                RecipeIngredient.objects.update_or_create(
                    recipe=recipe_instance,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'], defaults={'amount': ingredient['amount']}
                )

        @sync_to_async
        def create_tag():
            for tag in tags:
                RecipeTag(
                    recipe=recipe_instance,
                    tag=get_object_or_404(Tag, id=tag)
                ).save()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(
            create_ing(),
            create_tag()
        ))
        return recipe_instance

    def update(self, instance, validated_data):
        ingredients = validated_data.get('recipe_ingredients')
        tags = validated_data.get('tags')
        recipe_data = dict(
            filter(
                lambda kv: kv[0] not in ['recipe_ingredients', 'tags'],
                validated_data.items()
            )
        )
        instance = super().update(instance, recipe_data)

        @sync_to_async
        def update_ing():
            obj = RecipeIngredient.objects.filter(recipe=instance)
            obj.exclude(
                ingredient__in=[element['id'].id for element in ingredients]
            ).delete()
            for ingredient in ingredients:
                current_obj = obj.filter(ingredient=ingredient['id'].id)
                if current_obj.exists():
                    current_obj.update(
                        ingredient=ingredient['id'].id,
                        amount=ingredient['amount']
                    )
                else:
                    RecipeIngredient(
                        recipe=instance,
                        ingredient=ingredient['id'],
                        amount=ingredient['amount']
                    ).save()

        @sync_to_async
        def update_tag():
            recipe_tag = instance.recipe_tag.all()
            recipe_tag_values = recipe_tag.values_list('tag', flat=True)
            delete_id = list(set(recipe_tag_values).difference(
                tags))
            if len(delete_id) != 0:
                recipe_tag.filter(tag__in=delete_id).delete()
            if sorted(recipe_tag_values) != sorted((tags + delete_id)):
                for tag in tags:
                    current_obj = recipe_tag.filter(tag=tag)
                    if current_obj.exists():
                        current_obj.update(tag=get_object_or_404(Tag, id=tag))
                    else:
                        RecipeTag(
                            recipe=instance,
                            tag=get_object_or_404(Tag, id=tag)).save()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(
            update_ing(),
            update_tag()
        ))
        return instance

    def to_representation(self, instance):
        ingredients = self.fields['ingredients']
        ingredients_value = ingredients.to_representation(
            ingredients.get_attribute(instance)
        )
        text = self.fields['text']
        text_value = text.to_representation(
            text.get_attribute(instance)
        )
        cooking_time = self.fields['cooking_time']
        cooking_time_value = cooking_time.to_representation(
            cooking_time.get_attribute(instance)
        )
        image = self.fields['image']
        image_value = image.to_representation(
            image.get_attribute(instance)
        )
        author = self.fields['author']
        author_value = text.to_representation(
            author.get_attribute(instance)
        )
        return {
            'ingredients': ingredients_value,
            'tags': instance.recipe_tag.all().values_list('tag', flat=True),
            'text': text_value,
            'name': instance.name,
            'cooking_time': cooking_time_value,
            'image': image_value,
            'author': author_value
        }


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
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGetSerializer(ModelSerializer):
    ingredients = RelatedIngredientRecipeSerializer(
        source='recipe_ingredients', many=True
    )
    tags = TagSerializer(many=True, read_only=True)
    author = ProfileSerializer(read_only=True)
    is_favorited = serializers.serializers.SerializerMethodField(
        read_only=True
    )
    is_in_shopping_cart = serializers.serializers.SerializerMethodField(
        read_only=True
    )

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


class RecipeResponseSerializer(Serializer):
    id = serializers.serializers.IntegerField(read_only=True)
    name = serializers.serializers.CharField(read_only=True)
    image = serializers.serializers.ImageField(read_only=True)
    cooking_time = serializers.serializers.IntegerField(read_only=True)


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
    username = serializers.serializers.ReadOnlyField(
        source='ingredient.username'
    )
    first_name = serializers.serializers.ReadOnlyField(
        source='ingredient.first_name'
    )
    last_name = serializers.serializers.ReadOnlyField(
        source='ingredient.last_name'
    )

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name')


class RelatedRecipeSubscribeGetSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'


class RecipeSubscribeGetSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class SubscribeResponseSerializer(Serializer):
    id = serializers.serializers.IntegerField(read_only=True)
    email = serializers.serializers.CharField(read_only=True)
    username = serializers.serializers.CharField(read_only=True)
    first_name = serializers.serializers.CharField(read_only=True)
    last_name = serializers.serializers.CharField(read_only=True)
    is_subscribed = serializers.serializers.SerializerMethodField()
    recipes = serializers.serializers.SerializerMethodField()
    recipes_count = serializers.serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'

    def get_recipes(self, obj):
        queryset = obj.recipes.all()
        return RecipeSubscribeGetSerializer(
            queryset, many=True, context={'request': self.context['request']}
        ).data

    def get_recipes_count(self, obj):
        qs = obj.recipes.all()
        return qs.count()

    def get_is_subscribed(self, obj):
        return Subscribe.objects.filter(
            user=self.context['request'].user.id, author=obj
        ).exists()


class SubscribeGetSerializer(ModelSerializer):
    id = serializers.serializers.ReadOnlyField(source='author.id')
    email = serializers.serializers.ReadOnlyField(source='author.email')
    username = serializers.serializers.ReadOnlyField(source='author.username')
    first_name = serializers.serializers.ReadOnlyField(
        source='author.first_name'
    )
    last_name = serializers.serializers.ReadOnlyField(
        source='author.last_name'
    )
    is_subscribed = serializers.serializers.SerializerMethodField()
    recipes = serializers.serializers.SerializerMethodField()
    recipes_count = serializers.serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        limit = int(self.context['request'].query_params.get('recipes_limit'))
        queryset = obj.author.recipes.all()[:limit]
        return RecipeSubscribeGetSerializer(
            queryset, many=True, context={'request': self.context['request']}
        ).data

    def get_recipes_count(self, obj):
        limit = int(self.context['request'].query_params.get('recipes_limit'))
        qs = obj.author.recipes.all()[:limit]
        return qs.count()

    def get_is_subscribed(self, obj):
        return Subscribe.objects.filter(
            user=self.context['request'].user.id, author=obj.author
        ).exists()


class ShoppingListGetSerializer(ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')
