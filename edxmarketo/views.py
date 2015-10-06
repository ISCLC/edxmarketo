from django.http import HttpResponse
# from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie

from pythonmarketo.client import MarketoClient

from edxmarketo.app_settings import MARKETO_HOST, MARKETO_CLIENT_ID, MARKETO_CLIENT_SECRET


def get_marketo_client():
    """ get a Marketo Client using supplied auth params
    """

    mc = MarketoClient(host=MARKETO_HOST,
                       client_id=MARKETO_CLIENT_ID,
                       client_secret=MARKETO_CLIENT_SECRET)
    return mc


@login_required
@ensure_csrf_cookie
def test_marketo_connection(request):
    """
    Make sure we can authenticate
    """
    import pdb; pdb.set_trace()
    mc = get_marketo_client()
    try:
        mc.authenticate()
        return HttpResponse('Marketo Client authenticated successfully', status=200)
    except:
        return HttpResponse('Marketo Client could not authorize', status=400)
