from functools import partial

from django.test.utils import override_settings
from mock import patch
from mock_django.signals import mock_signal_receiver
# from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.signals import grading_event
from xmodule.modulestore.tests.django_utils import TEST_DATA_MOCK_MODULESTORE
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.factories import StudentModuleFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from opaque_keys.edx.locations import SlashSeparatedCourseKey

# from courseware.features.problems_setup import add_problem_to_course

# from capa.tests.response_xml_factory import (
#     ChoiceResponseXMLFactory,
#     MultipleChoiceResponseXMLFactory,
#     NumericalResponseXMLFactory,
#     OptionResponseXMLFactory,
#     StringResponseXMLFactory,
# )

from edxmarketo.tests.common import MICROSITE_CONFIG_ENABLED
from edxmarketo.signals import handlers


def mock_microsite_get_value(value, default, enabled):
    # mock out microsite get value so we don't need to worry about
    # middleware/requests here

    # TODO: couldn't figure out how to combine an override_settings decorator in the test
    # method with a patch context manager, so we use this with a partial passing in enabled
    if value == 'course_enable_marketo_integration':
        return enabled
    else:
        return MICROSITE_CONFIG_ENABLED['default'][value]


class FilesystemMarketoClient(object):

    def execute(self, method, **kwargs):

        def update_lead(**kwargs):
            """
            attrs are lookupField (str), lookupValue (str), values (dict)
            """
            pass

        def get_leads(**kwargs):
            """
            attrs are filtr (str), values (tuple), fields (tuple)
            """
            pass

        return eval(method(**kwargs))


@override_settings(
    MODULESTORE=TEST_DATA_MOCK_MODULESTORE
)
@patch('pythonmarketo.client.MarketoClient', FilesystemMarketoClient)
class TestMarketoIntegration(ModuleStoreTestCase):
    """
    Test iteration through student gradesets.
    """
    COURSE_ORG = "testorg"
    COURSE_NUMBER_YES = "101"
    COURSE_NUMBER_NO = "102"
    COURSE_DISPLAY_NAME_YES = "marketo_test"
    COURSE_DISPLAY_NAME_NO = "no_marketo_test"
    # COURSE_RUN = "2015_1"

    def setUp(self):
        """
        Create a course matching Marketo config, a course not matchings
        Marketo config and some users
        """
        self.make_courses()
        self.students = [
            UserFactory.create(username='student1_yeslead', email='dummy_lead@example.com'),
            UserFactory.create(username='student2_nolead', email='dummy_nolead@example.com'),
        ]
        self.problems = self.make_problems()
        self.student_modules = self.make_studentmodules()

    def make_courses(self):
        self.course_marketo = CourseFactory.create(
            org=self.COURSE_ORG,
            course=self.COURSE_NUMBER_YES,
            display_name=self.COURSE_DISPLAY_NAME_YES
        )
        self.course_nomarketo = CourseFactory.create(
            org=self.COURSE_ORG,
            course=self.COURSE_NUMBER_NO,
            display_name=self.COURSE_DISPLAY_NAME_NO
        )

    def make_problems(self):
        c1_key = SlashSeparatedCourseKey(self.course_marketo.org, self.course_marketo.number, self.course_marketo.display_name)
        c2_key = SlashSeparatedCourseKey(self.course_marketo.org, self.course_nomarketo.number, self.course_marketo.display_name)
        c1_prob = partial(c1_key.make_usage_key, u'problem')
        c2_prob = partial(c2_key.make_usage_key, u'problem')
        c1_chapter = partial(c1_key.make_usage_key, u'chapter')
        self.c1_p1_key = c1_prob('problem1')
        self.c1_p2_key = c1_prob('problem2')
        self.c1_p3_key = c1_prob('problem3')
        self.c1_p4_key = c1_prob('problem4')
        self.c1_p5_key = c1_prob('problem5')
        self.c1_p6_key = c1_prob('problem6')
        self.c1_p7_key = c1_prob('problem7')
        self.c2_p1_key = c2_prob('problem1')
        self.c1_chapter_key = c1_chapter('chapter1')

    def make_studentmodules(self):
        """
        Make studentmodules, per student (one with lead in Marketo, one without):
          - one non-problem to make sure we don't take action except on problems_setup
          - problem where course is not integrated with Marketo
          - problem where there is no response from student, just visited
          - probem where there is a response but it's not in a graded modulestore
          - problem where there is a response and the module is graded but the total possible score is zero
          - problem where there is a response and the module is graded, and we have a zero score, non-zero total
          - problem 1 where there is a response, the module is graded, non-zero score, non-zero total
          - problem 2 ...
          - problem 3 ...
          - problem 4 ...

        """
        students = self.students
        studentmodules = {
            'student1_yeslead': {
                # not a Marketo-integrated course
                'smod_1': StudentModuleFactory.create(student=students[0],
                                                      course_id=self.course_nomarketo.id,
                                                      grade=0,
                                                      max_grade=0,
                                                      state='{"student_answers":""}',
                                                      module_state_key=self.c2_p1_key),
                # yes Marketo course
                'smod_2': StudentModuleFactory.create(student=students[0],
                                                      course_id=self.course_marketo.id,
                                                      grade=1,
                                                      max_grade=1,
                                                      state='{"student_answers":""}',
                                                      module_state_key=self.c1_p1_key),
                # yes total grade, yes Marketo course, but not a graded problem
                # TODO: not sure this is testing the right thing
                'smod_3': StudentModuleFactory.create(student=students[0],
                                                      course_id=self.course_marketo.id,
                                                      grade=1,
                                                      max_grade=0,
                                                      state='{"student_answers":""}',
                                                      module_state_key=self.c1_p2_key),
                # yes total grade, yes Marketo course, zero score out of non-zero total
                'smod_4': StudentModuleFactory.create(student=students[0],
                                                      course_id=self.course_marketo.id,
                                                      grade=0,
                                                      max_grade=3,
                                                      state='{"student_answers":""}',
                                                      module_state_key=self.c1_p3_key),
                # yes total grade, yes Marketo course, non-zero score out of non-zero total
                'smod_5': StudentModuleFactory.create(student=students[0],
                                                      course_id=self.course_marketo.id,
                                                      grade=1,
                                                      max_grade=3,
                                                      state='{"student_answers":""}',
                                                      module_state_key=self.c1_p4_key),
                # yes total grade, yes Marketo course, non-zero score out of non-zero total
                'smod_6': StudentModuleFactory.create(student=students[0],
                                                      course_id=self.course_marketo.id,
                                                      grade=1,
                                                      max_grade=5,
                                                      state='{"student_answers":""}',
                                                      module_state_key=self.c1_p5_key),
                # yes total grade, yes Marketo course, non-zero score out of non-zero total
                'smod_7': StudentModuleFactory.create(student=students[0],
                                                      course_id=self.course_marketo.id,
                                                      grade=2,
                                                      max_grade=3,
                                                      state='{"student_answers":""}',
                                                      module_state_key=self.c1_p6_key),
                # yes total grade, yes Marketo course, non-zero score out of non-zero total
                'smod_8': StudentModuleFactory.create(module_type='chapter',
                                                      student=students[0],
                                                      course_id=self.course_marketo.id,
                                                      state='{"position":"1"}',
                                                      module_state_key=self.c1_chapter_key),
                # no answer given
                'smod_9': StudentModuleFactory.create(module_type='problem',
                                                      student=students[0],
                                                      course_id=self.course_marketo.id,
                                                      state='{}',
                                                      module_state_key=self.c1_p7_key), 


            },
            'student1_nolead': {
                'smod_1': StudentModuleFactory.create(student=students[1],
                                                      course_id=self.course_marketo.id,
                                                      grade=2,
                                                      max_grade=3,
                                                      state='{"student_answers":""}',
                                                      module_state_key=self.c1_p4_key),
            }

        }
        return studentmodules

    def test_handler_responds_to_signal(self):
        with mock_signal_receiver(grading_event) as dummy_handler:
            smodule = self.student_modules['student1_yeslead']['smod_7']
            grading_event.send(sender=smodule, module=smodule, grade=1, max_grade=1)
            dummy_handler.assert_called_once_with(signal=grading_event, sender=smodule, module=smodule, grade=1, max_grade=1)

    @patch('edxmarketo.signals.handlers.get_value', partial(mock_microsite_get_value, enabled=False))
    def test_dont_check_marketo_complete_if_disabled_for_microsite(self):
        with patch('edxmarketo.signals.handlers.cached_check_marketo_complete') as dummy_cached_check:
            smodule = self.student_modules['student1_yeslead']['smod_7']
            grading_event.send(sender=smodule, module=smodule, grade=smodule.grade, max_grade=smodule.max_grade)
            self.assertEquals(0, dummy_cached_check.call_count)

    @patch('edxmarketo.signals.handlers.get_value', partial(mock_microsite_get_value, enabled=True))
    def test_check_marketo_complete_if_enabled_for_microsite(self):
        with patch('edxmarketo.signals.handlers.cached_check_marketo_complete') as dummy_cached_check:
            smodule = self.student_modules['student1_yeslead']['smod_2']
            # we can't patch if we send signal, have to call receiver directly
            handlers.handle_check_marketo_completion_score(sender=smodule, module=smodule, grade=smodule.grade, max_grade=smodule.max_grade)
            # course_id, email, course_map
            dummy_cached_check.assert_called_once_with('testorg/101/marketo_test',
                                                       'dummy_lead@example.com',
                                                       {'testorg/101/marketo_test': 'Course_1_Completed__c'})

    @patch('edxmarketo.signals.handlers.get_value', partial(mock_microsite_get_value, enabled=True))
    def test_dont_check_if_course_not_integrated_with_marketo(self):
        with patch('edxmarketo.signals.handlers.cached_check_marketo_complete') as dummy_cached_check:
            smodule = self.student_modules['student1_yeslead']['smod_1']
            handlers.handle_check_marketo_completion_score(sender=smodule, module=smodule, grade=smodule.grade, max_grade=smodule.max_grade)
            self.assertEquals(0, dummy_cached_check.call_count)

    # def test_update_marketo_complete(self):
    #     course_map = {'testorg/101/marketo_test': 'Course_1_Completed__c'}
    #     update_marketo_complete(course_map, 'testorg/101/marketo_test', 'dummy_lead@example.com', complete=True)
    #     self.assertEquals

    @patch('edxmarketo.signals.handlers.get_value', partial(mock_microsite_get_value, enabled=True))
    def test_dont_check_for_completion_if_not_a_problem_module(self):
        with patch('edxmarketo.signals.handlers.cached_check_marketo_complete') as dummy_cached_check:
            smodule = self.student_modules['student1_yeslead']['smod_8']
            handlers.handle_check_marketo_completion_score(sender=smodule, module=smodule, grade=None, max_grade=None)
            self.assertEquals(0, dummy_cached_check.call_count)

    @patch('edxmarketo.signals.handlers.get_value', partial(mock_microsite_get_value, enabled=True))
    def test_dont_check_for_completion_if_problem_grade_is_zero(self):
        # if so, no way it can increase the Marketo complete score
        with patch('edxmarketo.signals.handlers.cached_check_marketo_complete') as dummy_cached_check:
            smodule = self.student_modules['student1_yeslead']['smod_4']
            handlers.handle_check_marketo_completion_score(sender=smodule, module=smodule, grade=smodule.grade, max_grade=smodule.max_grade)
            self.assertEquals(0, dummy_cached_check.call_count)

    @patch('edxmarketo.signals.handlers.get_value', partial(mock_microsite_get_value, enabled=True))
    def test_dont_check_for_completion_if_no_answer_submitted(self):
        # if so, no way it can increase the Marketo complete score
        with patch('edxmarketo.signals.handlers.cached_check_marketo_complete') as dummy_cached_check:
            smodule = self.student_modules['student1_yeslead']['smod_9']
            handlers.handle_check_marketo_completion_score(sender=smodule, module=smodule, grade=smodule.grade, max_grade=smodule.max_grade)
            self.assertEquals(0, dummy_cached_check.call_count)

    # tests to do
    # elements of system for course Marketo-complete:
    #  - caching works so we don't have to make a request to client if already stored values
    #  - getting overall course completion value of 70%+ for student/course
    #     - make sure that non-graded modules don't affect this
    #     - mock out get_score to return some different combos of (correct, total) tuple

    # test that Marketo course completion value for course with student at 70%+ grade gets
