from collections import defaultdict
import logging
import json

from django.conf import settings
from django.dispatch import receiver

from courseware.courses import get_course
from courseware.models import StudentModuleHistory
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor_internal
from courseware.grades import manual_transaction, get_score
from courseware.module_utils import yield_dynamic_descriptor_descendents
from courseware.signals import grading_event

from microsite_configuration.microsite import get_value  # keep as-is for test mocking

from student.signals import va_enrollment_event

from pythonmarketo.helper.exceptions import MarketoException
from keyedcache import cache_set, cache_get, cache_key, NotCachedError, cache_enabled, cache_enable

from edxmarketo.utils import get_marketo_client

logger = logging.getLogger(__name__)


MIN_SCORED_PERCENTAGE_FOR_MARKETO_COMPLETE = 70


def cached_check_marketo_complete(course_id, email, course_map):
    # email = 'bryanlandia+marketotest1@gmail.com'
    cachekey = cache_key('marketo_complete_cache',
                         course=course_id, email=email)
    try:
        value = cache_get(cachekey)
    except NotCachedError:
        value = None
    if value is None:
        # import pdb; pdb.set_trace()
        return check_marketo_complete(course_id, email, course_map)
    else:
        return value


def check_marketo_complete(course_id, email, course_map):
    """
    check if a course is already marked as complete in Marketo
    """
    # email = 'bryanlandia+marketotest1@gmail.com'
    # import pdb; pdb.set_trace()
    mkto_field_id = course_map[course_id]
    try:
        mc = get_marketo_client()
        complete = mc.execute(method='get_leads', filtr='email',
                              values=(email,), fields=(mkto_field_id,))
        if len(complete) > 1:
            raise MarketoException

        completeness = complete[0][mkto_field_id]
        if completeness:  # only cache True
            cachekey = cache_key('marketo_complete_cache',
                                 course=course_id, email=email)
            # our version of keyedcache doesn't recognize a cache is 
            # enabled in our multi-cache setup.
            if not cache_enabled():
                cache_enable()
            cache_set(cachekey, value=completeness)

        return completeness
    except MarketoException:
        # if we can't connect to Marketo or have some error with API,
        # don't continue trying to check completion
        return True


def update_marketo_complete(course_map, course_id, email, complete=True):
    """
    update Marketo course completeness field via REST API
    """
    logger.info(('Marking course {0} complete (70%+) in Marketo '
                 'for Lead with email {1}.').format(course_id, email))
    mkto_field_id = course_map[course_id]

    try:
        mc = get_marketo_client()
        status = mc.execute(method='update_lead', lookupField='email',
                            lookupValue=email,
                            values={mkto_field_id: complete})
        if status != 'updated':
            raise MarketoException("Update failed with status {0}".format(status))

    except MarketoException as e:
        logger.warn(('Failed to mark course {0} complete for Lead with '
                     'email {1}.  Error: {2}').format(course_id, email, e))


@receiver(grading_event, dispatch_uid='edxapp.edxmarketo.handle_check_marketo_completion_score')
def handle_check_marketo_completion_score(sender, module, grade, max_grade, **kwargs):
    """
    when a StudentModule is saved, check whether it is of a type that can affect
    our Marketo course completion percentage.  If so, calculate the new course
    completion percentage for the StudentModule's related Course, and then
    make a REST API request to Marketo to update the completion field.
    """
    if not grade:
        # a zero grade can't increase the Marketo complete score so no reason to check
        # we shouldn't get a False or None grade so we'll throw those out too
        return
    if not (get_value("course_enable_marketo_integration", None) and not \
            getattr(settings.FEATURES, "COURSE_ENABLE_MARKETO_INTEGRATION", None)
            ):
        return
    course_map = get_value("marketo_course_complete_field_map", None)
    if not course_map:
        logger.warn("Could not find Marketo course completion field map.")
        return

    instance = module
    student = instance.student

    if str(instance.course_id) not in course_map.keys():
        return

    # only continue for problem submissions
    state_dict = json.loads(instance.state) if instance.state else defaultdict(bool)

    if not state_dict or instance.module_type not in \
            StudentModuleHistory.HISTORY_SAVING_TYPES or \
            'student_answers' not in state_dict.keys():
        return

    if cached_check_marketo_complete(str(instance.course_id), student.email,
                                     course_map):
        # already marked complete.  don't need to keep checking
        return

    course = get_course(instance.course_id)

    logger.info(('Checking InterSystems Marketo completion score for course '
                '{0}, student {1}').format(instance.course_id, student))

    # TODO: make a Mocked REST API response
    # TODO: make call to REST API

    grading_context = course.grading_context

    # right now we don't care about state stored via the Submissions API
    # since this is only used by ORA2 and InterSystems doesn't use that
    # largely taken from courseware/grades.py

    non_zero_module_scores = 0
    total_scorable_modules = 0

    for section_format, sections in grading_context['graded_sections'].iteritems():

        for section in sections:
            if settings.DEBUG:
                section_descriptor = section['section_descriptor']
                section_name = section_descriptor.display_name_with_default
                logger.info('Checking completion of section {}'.format(section_name))

            def noop_track_function(event_type, event):
                pass

            def create_module(descriptor):
                '''creates an XModule instance given a descriptor'''
                with manual_transaction():
                    field_data_cache = FieldDataCache([descriptor], course.id,
                                                      student)

                # don't need tracking/xqueue but we have to pass something
                return get_module_for_descriptor_internal(
                    student, descriptor,
                    field_data_cache,
                    course.id,
                    track_function=noop_track_function,  # dummy
                    xqueue_callback_url_prefix='',  # dummy
                    request_token='')  # dummy

            for module_descriptor in yield_dynamic_descriptor_descendents(section_descriptor, create_module):

                (correct, total) = get_score(
                    course.id, student, module_descriptor, create_module
                )
                if correct is None and total is None:
                    continue

                graded = module_descriptor.graded
                if graded and total > 0:
                    total_scorable_modules += 1
                    if correct > 0:  # just has to have a non-zero score
                        non_zero_module_scores += 1

        if total_scorable_modules > 0:
            nonzero_modules = float(non_zero_module_scores) / float(total_scorable_modules)

            if nonzero_modules * 100 >= \
                    MIN_SCORED_PERCENTAGE_FOR_MARKETO_COMPLETE:

                # inform Marketo that this course is 'complete'
                update_marketo_complete(course_map, str(instance.course_id), student.email)


@receiver(va_enrollment_event)
def handle_va_enrollment_event(sender, student, **kwargs):
    """
    set Marketo VA Learning Path Enrolled for Lead corresponding to user
    """
    if not (get_value("course_enable_marketo_integration", None) and not \
            getattr(settings.FEATURES, "COURSE_ENABLE_MARKETO_INTEGRATION", None)
            ):
        return

    logger.info(('Setting VA Learning Path Enrolled for Lead with email {0}.').format(student.email))
    mkto_field_id = get_value("marketo_va_enrollment_field_id", None)
    if not mkto_field_id:
        logger.warn(('Can\'t set VA Learning Path Enrolled for Lead with email {0}.').format(student.email))

    try:
        mc = get_marketo_client()
        status = mc.execute(method='update_lead', lookupField='email',
                            lookupValue=student.email,
                            values={mkto_field_id: True})
        if status != 'updated':
            raise MarketoException("Update failed with status {0}".format(status))

    except MarketoException as e:
        logger.warn(('Can\'t set VA Learning Path Enrolled for Lead with email {0}.').format(student.email))
