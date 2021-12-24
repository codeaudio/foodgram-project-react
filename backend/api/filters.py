from django_filters import rest_framework as filters

from .models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.Filter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ['tags']
