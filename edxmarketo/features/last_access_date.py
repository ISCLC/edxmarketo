from datetime import datetime

from mock import patch
from django.test.utils import override_settings
from lettuce import world, step, before
from nose.tools import assert_equals
# from courseware.features.common import add_tab_to_course

from edxmarketo.tests.common import MICROSITE_CONFIG_ENABLED, MICROSITE_CONFIG_DISABLED


MOCK_MARKETO_STORAGE = {
    "testorg/101/Marketo_Test_last_access": "original",
    "testorg/101/No_Marketo_last_access": "original"
}


@before.each_scenario
def setUp(scenario):
    world.scenario_dict['MOCK_MARKETO_STORAGE'] = MOCK_MARKETO_STORAGE


@step(u'I am viewing a course (with|without) Marketo connection and Marketo integration is (enabled|disabled) for the microsite')
def view_course(step, course_marketo, microsite_marketo):
    # import pdb; pdb.set_trace()
    is_marketo_course = course_marketo == 'with' and True or False
    create_course(is_marketo_course)

    microsite_setting = microsite_marketo and MICROSITE_CONFIG_ENABLED or MICROSITE_CONFIG_DISABLED
    with override_settings(MICROSITE_CONFIGURATION=microsite_setting):
        create_user_and_visit_course()
        # Wait for the our AJAX call to update Marketo to complete
        world.wait_for_ajax_complete()


@step(u"the Marketo last accessed date field stores (today's|original) date")
def check_marketo_last_access_date(step, expected):
    today = str(datetime.now().date())
    last_access_val = world.scenario_dict['MOCK_MARKETO_STORAGE']['{}_last_access'.format(world.scenario_dict['COURSE'].id)]

    if expected == "today's":
        # TODO: this could fail if we change days while running the test.
        assert_equals(today, last_access_val)
    else:
        assert_equals("original", last_access_val)


def create_course(is_marketo_course):
    world.clear_courses()
    name = is_marketo_course and 'Marketo Test' or 'No Marketo'
    world.scenario_dict['COURSE'] = world.CourseFactory.create(
        org='testorg', number='101', display_name=name
    )

# @patch()
def create_user_and_visit_course():
    # TODO:  this needs to update our mocked storage
    world.register_by_course_key(world.scenario_dict['COURSE'].id)
    world.log_in()
    world.visit(u'/courses/{}/courseware/'.format(world.scenario_dict['COURSE'].id))
