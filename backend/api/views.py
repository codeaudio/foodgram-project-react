from dataclasses import asdict
from threading import Thread

from django.contrib.auth import logout
from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import authentication as auth
from rest_framework import permissions, generics
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt import authentication as jwt_auth
from rest_framework_simplejwt.views import TokenObtainPairView

from .filters import RecipeFilter
from .models import Tag, Ingredient, Recipe, RecipeIngredient, RecipeTag, RecipeFavorite, Subscribe, \
    ShoppingList
from .pagination import CustomPagination
from .permissions import OwnerPermission
from .response import ShoppingListGetResponse
from .serializers import CustomSerializer, TagSerializer, \
    IngredientSerializer, RecipeGetSerializer, RecipePostOrUpdateSerializer, \
    RecipeFavoriteSerializer, SubscribeSerializer, SubscribeGetSerializer, ShoppingListGetSerializer, ProfileSerializer, \
    ProfileCreateSerializer
from .utils import get_file_from_base64, render_to_pdf


class CustomUserViewSet(UserViewSet):

    def get_serializer_class(self):
        if self.action == 'list':
            self.pagination_class = CustomPagination
            return ProfileSerializer
        if self.request.method == 'GET':
            return ProfileSerializer
        if self.action == 'create':
            return ProfileCreateSerializer


@api_view(['POST'])
def logout_user(request):
    logout(request)
    return Response('null', status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomSerializer


class TagViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filterset_class = RecipeFilter

    def get_authenticators(self):

        request = Request(
            self.request,
            parsers=self.get_parsers(),
            authenticators=super(RecipeViewSet, self).get_authenticators(),
            negotiator=self.get_content_negotiator(),
            parser_context=self.get_parser_context(self.request)
        )
        try:
            if request.user.is_anonymous and self.request.method == 'GET':
                return [auth.SessionAuthentication()]
        except:
            return [auth.SessionAuthentication()]
        return [jwt_auth.JWTAuthentication()]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [OwnerPermission()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH', 'POST']:
            return RecipePostOrUpdateSerializer
        return RecipeGetSerializer

    def update(self, request, *args, **kwargs):
        recipe_instance = self.get_object()
        serializer = self.get_serializer(recipe_instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        ingredients = serializer.validated_data.get('ingredients')
        tags = serializer.validated_data.get('tags')
        if 'image' in serializer.validated_data:
            recipe_instance.image = get_file_from_base64(serializer.validated_data.get('image'))
        recipe_instance.text = serializer.validated_data.get('text')
        recipe_instance.name = serializer.validated_data.get('name')
        recipe_instance.cooking_time = serializer.validated_data.get('cooking_time')
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
                        ingredient=get_object_or_404(Ingredient, id=ingredient.get('id')),
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
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = RecipeFavorite.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RecipeFavoriteSerializer
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        data = {
            'recipe': self.kwargs.get('recipe_id'),
            'user': request.user.id,
            'author': get_object_or_404(Recipe, id=self.kwargs.get('recipe_id')).author.id
        }
        serializer = self.get_serializer_class()(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'is_favorited': True}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        data = {
            'recipe': self.kwargs.get('recipe_id'),
            'user': request.user.id,
            'author': get_object_or_404(Recipe, id=self.kwargs.get('recipe_id')).author.id
        }
        serializer = self.get_serializer_class()(data=data)
        serializer.is_valid(raise_exception=True)
        self.queryset.filter(
            recipe=serializer.validated_data.get('recipe'),
            user=serializer.validated_data.get('user'),
            author=serializer.validated_data.get('author')
        ).delete()
        return Response({'is_favorited': False}, status=status.HTTP_200_OK)


class SubscribeViewSet(viewsets.ModelViewSet):
    queryset = Subscribe.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscribeSerializer
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        data = {
            'user': request.user.id,
            'author': self.kwargs.get('author_id')
        }
        serializer = self.get_serializer_class()(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"is_subscribed": True}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        data = {
            'user': request.user.id,
            'author': self.kwargs.get('author_id')
        }
        serializer = self.get_serializer_class()(data=data)
        serializer.is_valid(raise_exception=True)
        self.queryset.filter(
            user=serializer.validated_data.get('user'),
            author=serializer.validated_data.get('author')
        ).delete()
        return Response({"is_subscribed": False}, status=status.HTTP_204_NO_CONTENT)


class SubscribeListView(generics.ListAPIView):
    queryset = Subscribe.objects.all()
    serializer_class = SubscribeGetSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return self.queryset.filter(
            user=self.request.user.id
        )


class ShoppingListViewSet(viewsets.ModelViewSet):
    queryset = ShoppingList.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ShoppingListGetSerializer
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        data = {
            'user': request.user.id,
            'recipe': self.kwargs.get('recipe_id')
        }
        serializer = self.get_serializer_class()(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        recipe = serializer.validated_data.get('recipe')
        return Response(asdict(ShoppingListGetResponse(recipe.id, recipe.name, self.request.META.get(
            'wsgi.url_scheme') + '://' + self.request.get_host() + '/mediadjango/' + str(recipe.image),
                                                       recipe.cooking_time)), status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        data = {
            'user': request.user.id,
            'recipe': self.kwargs.get('recipe_id')
        }
        serializer = self.get_serializer_class()(data=data)
        serializer.is_valid(raise_exception=True)
        self.queryset.filter(
            user=serializer.validated_data.get('user'),
            recipe=serializer.validated_data.get('recipe')
        ).delete()
        return Response({'is_in_shopping_cart': False}, status=status.HTTP_204_NO_CONTENT)


class ShoppingDownloadView(generics.ListAPIView):
    queryset = ShoppingList.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ShoppingListGetSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return self.queryset.filter(
            user=self.request.user.id
        )

    def get(self, request, *args, **kwargs):
        context = {
            'user_username': self.request.user.username,
            'shopping_list': Recipe.objects.filter(
                id__in=self.queryset.values_list('recipe', flat=True)).select_related('author').prefetch_related(
                'ingredients'),
        }
        pdf = render_to_pdf('shopping_list.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            return response
        return Response(status=status.HTTP_400_BAD_REQUEST)
