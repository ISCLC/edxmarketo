from django.http import HttpResponse
# from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie

from edxmarketo.utils import get_marketo_client


@login_required
@ensure_csrf_cookie
def test_marketo_connection(request):
    """
    Make sure we can authenticate
    """
    mc = get_marketo_client()
    try:
        mc.authenticate()
        return HttpResponse('Marketo Client authenticated successfully', status=200)
    except:
        return HttpResponse('Marketo Client could not authorize', status=400)
