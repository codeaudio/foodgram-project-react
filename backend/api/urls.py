from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (logout_user, CustomTokenObtainPairView, RecipeViewSet,
                    TagViewSet, IngredientViewSet, FavoriteViewSet,
                    SubscribeViewSet, SubscribeListView, ShoppingListViewSet,
                    ShoppingDownloadView)

router_v1 = DefaultRouter()
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('recipes/download_shopping_cart/', ShoppingDownloadView.as_view(), name='download_shopping_cart'),
    path('users/subscriptions/', SubscribeListView.as_view(), name='subscriptions'),
    path('recipes/<str:recipe_id>/shopping_cart/', ShoppingListViewSet.as_view({'post': 'create', 'delete': 'destroy'}), name='shopping'),
    path('recipes/<str:recipe_id>/favorite/', FavoriteViewSet.as_view({'post': 'create', 'delete': 'destroy'}), name='favorite'),
    path('users/<str:author_id>/subscribe/', SubscribeViewSet.as_view({'post': 'create', 'delete': 'destroy'}), name='subscribe'),
    path(
        'login/',
        CustomTokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),
    path(
        'logout/',
        logout_user,
        name='logout'
    ),
    path('', include(router_v1.urls))
]
