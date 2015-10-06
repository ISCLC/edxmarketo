from django.conf.urls import url
from django.conf import settings


if settings.DEBUG:
    urlpatterns = [
        url(r'^marketo_test$', 'edxmarketo.views.test_marketo_connection'),
    ]
