from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .views import logout_user, CustomTokenObtainPairView, RecipeViewSet, TagViewSet, IngredientViewSet

router_v1 = DefaultRouter()
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
urlpatterns = [
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
