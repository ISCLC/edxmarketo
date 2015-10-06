from collections import defaultdict
import logging
import json

from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save

from courseware.courses import get_course
from courseware.models import StudentModule, StudentModuleHistory
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor_internal
from courseware.grades import manual_transaction, get_score
from courseware.module_utils import yield_dynamic_descriptor_descendents

logger = logging.getLogger(__name__)


MIN_SCORED_PERCENTAGE_FOR_MARKETO_COMPLETE = 5  # 70


@receiver(post_save, sender=StudentModule, dispatch_uid='edxapp.edxmarketo.handle_check_marketo_completion_score')
def handle_check_marketo_completion_score(sender, instance, **kwargs):
    """
    when a StudentModule is saved, check whether it is of a type that can affect
    our Marketo course completion percentage.  If so, calculate the new course
    completion percentage for the StudentModule's related Course, and then
    make a REST API request to Marketo to update the completion field.
    """
    # import pdb; pdb.set_trace()

    # only continue for problem submissions
    state_dict = json.loads(instance.state) if instance.state else defaultdict(bool)
    if not state_dict or instance.module_type not in \
            StudentModuleHistory.HISTORY_SAVING_TYPES or \
            'input_state' not in state_dict.keys():
        return
        if state_dict['done']:
            return

    import pdb; pdb.set_trace()
    course = get_course(instance.course_id)
    student = instance.student
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
                logger.debug('Checking completion of section {}'.format(section_name))

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
                    if correct > 0:
                        non_zero_module_scores += 1

        if total_scorable_modules > 0:
            # import pdb; pdb.set_trace()
            nonzero_modules = float(non_zero_module_scores) / float(total_scorable_modules)

            if nonzero_modules * 100 >= \
                    MIN_SCORED_PERCENTAGE_FOR_MARKETO_COMPLETE:

                # inform Marketo that this course is 'complete'
                logger.info(('Marking course {0} complete (70%+) in Marketo '
                             'for student {1}.').format(instance.course_id, student))
