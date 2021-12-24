from threading import Thread

from django.contrib.auth import get_user_model, logout
from django.core.files.base import ContentFile
from djoser.views import UserViewSet
from rest_framework import permissions
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .filters import RecipeFilter
from .models import Tag, Ingredient, Recipe, RecipeIngredient, RecipeTag
from .pagination import CustomPagination
from .serializers import CustomSerializer, TagSerializer, \
    IngredientSerializer, RecipeGetSerializer, RecipeUpdateSerializer, \
    RelatedIngredientRecipeUpdateSerializer, RelatedTagRecipeUpdateSerializer, RecipePostOrUpdateSerializer
import base64

from .utils import get_file_from_base64


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPagination


@api_view(['POST'])
def logout_user(request):
    logout(request)
    return Response('null', status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH', 'POST']:
            return RecipePostOrUpdateSerializer
        return RecipeGetSerializer

    def update(self, request, *args, **kwargs):
        recipe_instance = self.get_object()
        serializer = self.get_serializer(recipe_instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        current_obj = Recipe.objects.filter(id=serializer.validated_data.get('id'))
        ingredients = serializer.validated_data.get('ingredients')
        tags = serializer.validated_data.get('tags')
        recipe_instance.image = get_file_from_base64(serializer.validated_data.get('image'))
        recipe_instance.text = serializer.validated_data.get('text'),
        recipe_instance.recipe_instance. name = serializer.validated_data.get('name'),
        recipe_instance.cooking_time = serializer.validated_data.get('cooking_time'),
        recipe_instance.save()


        def update_ing():
            obj = RecipeIngredient.objects.filter(recipe=recipe_instance)

            if len(ingredients) < obj.count():
                obj.exclude(
                    ingredient__in=[
                        v.id for element in
                        ingredients for k, v in element.items()
                        if k == 'id'
                    ]
                ).delete()
            for ingredient in ingredients:
                current_obj = obj.filter(ingredient=ingredient.get('id'))
                if current_obj.exists():
                    current_obj.update(
                        ingredient=ingredient.get('id'),
                        amount=ingredient.get('amount')
                    )
                else:
                    RecipeIngredient(
                        recipe=recipe_instance,
                        ingredient=ingredient.get('id'),
                        amount=ingredient.get('amount')
                    ).save()

        def update_tag():
            obj = RecipeTag.objects.filter(recipe=recipe_instance)
            recipe_tag = list(recipe_instance.recipetag_set.all().values_list('tag', flat=True))
            delete_id = list(set(recipe_tag).difference(
                tags))
            if len(delete_id) != 0:
                obj.filter(tag__in=delete_id).delete()

            if sorted(recipe_tag) != sorted((tags + delete_id)):
                for tag in tags:
                    current_obj = obj.filter(tag=tag)
                    if current_obj.exists():
                        current_obj.update(tag=get_object_or_404(Tag, id=tag))
                    else:
                        RecipeTag(
                            recipe=recipe_instance,
                            tag=get_object_or_404(Tag, id=tag)).save()

        def update_rows():
            th_ing, th_tag = Thread(target=update_ing), Thread(target=update_tag)
            th_ing.start(), th_tag.start()
            th_ing.join(), th_tag.join()

        update_rows()

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        ingredients = serializer.validated_data.get('ingredients')
        tags = serializer.validated_data.get('tags')
        recipe_instance = Recipe(
            text=serializer.validated_data.get('text'),
            name=serializer.validated_data.get('name'),
            cooking_time=serializer.validated_data.get('cooking_time'),
            author=self.request.user,
            image=get_file_from_base64(serializer.validated_data.get('image'))
        )
        recipe_instance.save()

        def create_ing():
            for ingredient in ingredients:
                RecipeIngredient(
                    recipe=recipe_instance,
                    ingredient=get_object_or_404(Ingredient, id=ingredient.get('id')),
                    amount=ingredient.get('amount')).save()

        def create_tag():
            for tag in tags:
                RecipeTag(
                    recipe=recipe_instance,
                    tag=get_object_or_404(Tag, id=tag)
                ).save()

        def create_rows():
            th_ing, th_tag = Thread(target=create_ing), Thread(target=create_tag)
            th_ing.start(), th_tag.start()
            th_ing.join(), th_tag.join()

        create_rows()
        return Response(status=status.HTTP_200_OK)
