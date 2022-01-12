from rest_framework import serializers

from .utils import Converter


class Base64ImageField(serializers.ImageField, Converter):

    def to_internal_value(self, data):
        if 'data:' in data and ';base64,' in data:
            return super().to_internal_value(self.get_file_from_base64(data))
