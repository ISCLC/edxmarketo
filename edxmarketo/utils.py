from os import environ
import logging

from django.conf import settings
from microsite_configuration import microsite

try:
    from edxmarketo.app_settings import MARKETO_HOST, MARKETO_CLIENT_ID, MARKETO_CLIENT_SECRET
except ImportError:
    if environ.get('DJANGO_SETTINGS_MODULE') in (
            'lms.envs.acceptance', 'lms.envs.test',
            'cms.envs.acceptance', 'cms.envs.test'):
        MARKETO_HOST = MARKETO_CLIENT_ID = MARKETO_CLIENT_SECRET = ''

# if settings.DEBUG:
#     from edxmarketo.tests import MockMarketoClient as MarketoClient
# else:
#     from pythonmarketo.client import MarketoClient

from pythonmarketo.client import MarketoClient

logger = logging.getLogger(__name__)


def get_marketo_client():
    """ get a Marketo Client using supplied auth params
    """
    mc = MarketoClient(host=MARKETO_HOST,
                       client_id=MARKETO_CLIENT_ID,
                       client_secret=MARKETO_CLIENT_SECRET)
    return mc


def is_marketo_course(course_id):
    if not microsite.get_value("course_enable_marketo_integration") and not \
            getattr(settings.FEATURES, "COURSE_ENABLE_MARKETO_INTEGRATION", None):
        return False

    course_map = microsite.get_value("marketo_course_access_field_map", None)
    if not course_map:
            logger.warn("Could not find Marketo course access field map.")
            return False

    if course_id in course_map.keys():
        return True
    else:
        return False
