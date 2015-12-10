from os import environ

from django.conf import settings

MOCK_MARKETO_ONLY = False

try:
    AUTH_TOKENS = settings.AUTH_TOKENS
    ENV_TOKENS = settings.ENV_TOKENS

    MARKETO_HOST = AUTH_TOKENS.get('EDXAPP_MARKETO_HOST', None)
    MARKETO_CLIENT_ID = AUTH_TOKENS.get('EDXAPP_MARKETO_CLIENT_ID', None)
    MARKETO_CLIENT_SECRET = AUTH_TOKENS.get('EDXAPP_MARKETO_CLIENT_SECRET', None)
    MARKETO_TOKEN = AUTH_TOKENS.get('EDXAPP_MARKETO_TOKEN', None)

except AttributeError:
    # these won't be available in test, and we mock out Marketo
    if environ.get('DJANGO_SETTINGS_MODULE') in (
            'lms.envs.acceptance', 'lms.envs.test',
            'cms.envs.acceptance', 'cms.envs.test'):
        pass
    else:
        raise
