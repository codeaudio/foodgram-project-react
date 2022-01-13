from django.contrib.auth import logout
from django.db.models import F
from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import authentication as auth
from rest_framework import permissions, generics
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt import authentication as jwt_auth
from rest_framework_simplejwt.views import TokenObtainPairView

from .custom_mixin import CustomMixin, CustomCreateDestroyViewSet
from .filters import RecipeFilter, IngredientFilterSet
from .models import (Tag, Ingredient, Recipe,
                     RecipeFavorite, Subscribe,
                     ShoppingList)
from .pagination import CustomPagination
from .permissions import OwnerPermission
from .serializers import (CustomSerializer, TagSerializer,
                          IngredientSerializer, RecipeGetSerializer,
                          RecipePostOrUpdateSerializer,
                          RecipeFavoriteSerializer, SubscribeSerializer,
                          SubscribeGetSerializer,
                          ShoppingListGetSerializer, ProfileSerializer,
                          ProfileCreateSerializer, RecipeResponseSerializer,
                          SubscribeResponseSerializer)
from .utils import render_to_pdf


class CustomUserViewSet(UserViewSet):

    def get_permissions(self):
        if self.action == 'retrieve':
            return [permissions.AllowAny()]
        return super().get_permissions()

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


class IngredientViewSet(CustomMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilterSet


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


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = RecipeFavorite.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RecipeFavoriteSerializer
    response_serializer_class = RecipeResponseSerializer
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        data = {
            'recipe': self.kwargs.get('recipe_id'),
            'user': request.user.id,
            'author': get_object_or_404(
                Recipe,
                id=self.kwargs.get('recipe_id')
            ).author.id
        }
        serializer = self.get_serializer_class()(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.response_serializer_class(
            serializer.validated_data.get('recipe'),
            context={'request': request}).data, status=status.HTTP_200_OK
                        )

    def destroy(self, request, *args, **kwargs):
        data = {
            'recipe': self.kwargs.get('recipe_id'),
            'user': request.user.id,
            'author': get_object_or_404(
                Recipe,
                id=self.kwargs.get('recipe_id')
            ).author.id
        }
        serializer = self.get_serializer_class()(data=data)
        serializer.is_valid(raise_exception=True)
        self.queryset.filter(
            recipe=serializer.validated_data.get('recipe'),
            user=serializer.validated_data.get('user'),
            author=serializer.validated_data.get('author')
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeViewSet(CustomCreateDestroyViewSet):
    queryset = Subscribe.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscribeSerializer
    response_serializer_class = SubscribeResponseSerializer
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        data = {
            'user': request.user.id,
            'author': self.kwargs.get('author_id')
        }
        return super().create(
            request, data, self.response_serializer_class,
            'author', *args, **kwargs
        )

    def destroy(self, request, *args, **kwargs):
        data = {
            'user': request.user.id,
            'author': self.kwargs.get('author_id')
        }
        obj = self.queryset.filter(
            user=data.get('user'),
            author=data.get('author')
        )
        return super().destroy(
            request, data, obj, *args, **kwargs
        )


class SubscribeListView(generics.ListAPIView):
    queryset = Subscribe.objects.all()
    serializer_class = SubscribeGetSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return self.queryset.filter(
            user=self.request.user.id
        )


class ShoppingListViewSet(CustomCreateDestroyViewSet):
    queryset = ShoppingList.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ShoppingListGetSerializer
    response_serializer_class = RecipeResponseSerializer
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        data = {
            'user': request.user.id,
            'recipe': self.kwargs.get('recipe_id')
        }
        return super().create(
            request, data, self.response_serializer_class,
            'recipe', *args, **kwargs
        )

    def destroy(self, request, *args, **kwargs):
        data = {
            'user': request.user.id,
            'recipe': self.kwargs.get('recipe_id')
        }
        obj = self.queryset.filter(
            user=data.get('user'),
            recipe=data.get('recipe')
        )
        return super(ShoppingListViewSet, self).destroy(
            request, data, obj, *args, **kwargs
        )


class ShoppingDownloadView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ShoppingListGetSerializer
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        context = {
            'user_username': self.request.user.username,
            'shopping_list': Recipe.objects.filter(
                id=F('shopped__recipe'), shopped__user_id=self.request.user.id
            ).select_related(
                'author'
            ).prefetch_related(
                'ingredients'
            ),
        }
        pdf = render_to_pdf('shopping_list.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            return response
        return Response(status=status.HTTP_400_BAD_REQUEST)
