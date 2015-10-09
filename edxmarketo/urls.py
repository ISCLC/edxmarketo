from django.conf.urls import url
from django.conf import settings


urlpatterns = [
    url(r'^marketo_course_access$', 'edxmarketo.views.set_marketo_course_access_date'),
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^marketo_test$', 'edxmarketo.views.test_marketo_connection'),
    ]
