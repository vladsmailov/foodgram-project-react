"""Mixins for api_yamdb."""
from rest_framework import mixins, viewsets


class CreateListDestroyViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """CreateListDestroyViewSet definition."""

    pass
