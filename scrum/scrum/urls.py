# from django.conf.urls import include, urls
from django.conf.urls import url, include

from django.views.generic import TemplateView

from rest_framework.authtoken.views import obtain_auth_token
from board.urls import router

urlpatterns = [
    url(r'^api/token/', obtain_auth_token, name='api-token'),
    url(r'^api/', include(router.urls)),
    url(r'^$', TemplateView.as_view(template_name='board/index.html'))
]