import django_filters
from django_filters import rest_framework as filters

from .models import Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = filters.Filter(field_name='author__id')
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited',
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart',
    )

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(recipe_favorite__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopped__user=self.request.user.id)
        return queryset

    class Meta:
        model = Recipe
        fields = ('tags', 'is_favorited', 'author')


class IngredientFilterSet(filters.FilterSet):
    name = filters.Filter(field_name='name', lookup_expr='contains')

    class Meta:
        model = Ingredient
        fields = ('name',)
