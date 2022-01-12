from rest_framework import viewsets, mixins, status
from rest_framework.response import Response


class CustomMixin(viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin):
    pass


class CustomCreateDestroyViewSet(viewsets.ModelViewSet):

    def create(self, request, data=None, response_serializer=None, response_data=None, *args, **kwargs):
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(response_serializer(
            serializer.validated_data.get(response_data),
            context={'request': request}).data, status=status.HTTP_200_OK)

    def destroy(self, request, data=None, obj=None, response_data=None, *args, **kwargs):
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
