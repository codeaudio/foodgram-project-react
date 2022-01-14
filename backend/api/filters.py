import django_filters
from django_filters import rest_framework as filters

from .models import Recipe, RecipeFavorite, ShoppingList, Ingredient


class RecipeFilter(filters.FilterSet):
    tags = filters.Filter(field_name='tags__slug', lookup_expr='contains')
    author = filters.Filter(field_name='author__id')
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited',
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart',
    )

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(
                id__in=list(RecipeFavorite.objects.filter(
                    user=self.request.user.id).values_list('recipe', flat=True)
                            )
            )
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(
                id__in=list(ShoppingList.objects.filter(
                    user=self.request.user.id).values_list('recipe', flat=True)
                            )
            )
        return queryset

    class Meta:
        model = Recipe
        fields = ('tags', 'is_favorited', 'author')


class RecipesLimit(django_filters.Filter):
    def filter(self, queryset, value):
        if value is not None:
            return queryset[:value]
        return queryset


class RecipesLimitFilterSet(filters.FilterSet):
    recipes = django_filters.NumberFilter(
        method='filter_recipes',
    )

    def filter_recipes(self, queryset, name, value):
        return queryset[:value]


class IngredientFilterSet(filters.FilterSet):
    name = filters.Filter(field_name='name', lookup_expr='contains')

    class Meta:
        model = Ingredient
        fields = ('name',)
