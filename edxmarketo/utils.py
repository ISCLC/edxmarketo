# from django.conf import settings

from edxmarketo.app_settings import MARKETO_HOST, MARKETO_CLIENT_ID, MARKETO_CLIENT_SECRET

# if settings.DEBUG:
#     from edxmarketo.tests import MockMarketoClient as MarketoClient
# else:
#     from pythonmarketo.client import MarketoClient

from pythonmarketo.client import MarketoClient


def get_marketo_client():
    """ get a Marketo Client using supplied auth params
    """
    mc = MarketoClient(host=MARKETO_HOST,
                       client_id=MARKETO_CLIENT_ID,
                       client_secret=MARKETO_CLIENT_SECRET)
    return mc
