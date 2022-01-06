from rest_framework import viewsets, mixins


class CustomMixin(viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin):
    pass
