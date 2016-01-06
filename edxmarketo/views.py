import logging
import datetime

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from util.json_request import JsonResponse
from microsite_configuration import microsite

from pythonmarketo.helper.exceptions import MarketoException
from edxmarketo.utils import get_marketo_client


logger = logging.getLogger(__name__)


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


@login_required
@require_POST
@ensure_csrf_cookie
def set_marketo_course_access_date(request):
    """
    AJAX call from course_navigation
    Set the last accessed date for this course in Marketo via REST API
    """
    errstr = ''
    email = request.user.email
    course_id = request.POST.get('course_id')
    if not email and course_id:
        return JsonResponse({
            "success": False,
            "error": 'Failed to update course last access date.  No course id or user',
        }, status=500)
    try:
        mc = get_marketo_client()
        now = str(datetime.datetime.now())
        mkto_course_field_id = microsite.get_value("marketo_course_access_field_map")[course_id]
        mkto_path_field_id = microsite.get_value("marketo_va_activity_field")
        status = mc.execute(method='update_lead', lookupField='email',
                            lookupValue=email,
                            values={mkto_course_field_id: now,
                                    mkto_path_field_id: now})
        if status == 'updated':
            return JsonResponse({
                "success": True
            }, status=200)


    except MarketoException as e:
        errstr = e

    logger.warn(('Failed to mark course {0} and Learning Path access date for Lead with '
                 'email {1}.  Error: {2}').format(course_id, email, errstr))

    return JsonResponse({
        "success": False,
        "error": 'Failed to update course or learning path last access date',
    }, status=200)
