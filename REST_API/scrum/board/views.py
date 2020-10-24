from django.contrib.auth import get_user_model
from rest_framework import viewsets, authentication, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend # Bc it is not in filters, the above line
from .forms import TaskFilter
from .models import Sprint, Task
from .serializers import SprintSerializer, TaskSerializer, UserSerializer

User = get_user_model()

class DefaultsMixin(object):
    """ Default settings for view authentication, permissions, filtering and pagination """
    
    authentication_classes = (
        authentication.BasicAuthentication,
        authentication.TokenAuthentication,
    )
    permissions_classes = (
        permissions.IsAuthenticated,
    )
    paginate_by = 25
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    filter_backends = (
        DjangoFilterBackend, # Here just add it since I have imported it before
        filters.SearchFilter,
        filters.OrderingFilter,
    )

class SprintViewSet(DefaultsMixin, viewsets.ModelViewSet):
    """ API endpoint for listing and creating sprints """

    queryset = Sprint.objects.order_by('end')
    serializer_class = SprintSerializer
    search_fields = ('name',)
    ordering_fields = ('end', 'name', )

class TaskViewSet(DefaultsMixin, viewsets.ModelViewSet):
    """ API endpoint for listing and creating tasks """

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    # filter_class = TaskFilter
    search_fields = ('name', 'description', )
    ordering_fields = ('name', 'order', 'started', 'due', 'completed', )

class UserViewSet(DefaultsMixin, viewsets.ReadOnlyModelViewSet):
    """ API endpoint for listing users """

    lookup_field = User.USERNAME_FIELD
    lookup_url_kwarg = User.USERNAME_FIELD
    queryset = User.objects.order_by(User.USERNAME_FIELD)
    serializer_class = UserSerializer
    search_fields = (User.USERNAME_FIELD)