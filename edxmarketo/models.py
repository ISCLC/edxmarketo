"""
WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py schemamigration edxmarketo --auto description_of_your_change
3. Add the migration file created in edxmarketo/migrations/


ASSUMPTIONS: modules have unique IDs, even across different module_types

"""
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save

from xmodule_django.models import CourseKeyField, LocationKeyField


class StudentModuleMarketo(models.Model):
    """
    Keeps student state of "Marketo Completion" for a given Course module.
    We store this in edX db so we don't have to connect to Marketo API 
    every time something of interest happens with a Course.
    """
    MODEL_TAGS = ['course_id', 'module_type']

    # Key used to share state. This is the XBlock usage_id
    module_state_key = LocationKeyField(max_length=255, db_index=True, db_column='module_id')
    student = models.ForeignKey(User, db_index=True)

    course_id = CourseKeyField(max_length=255, db_index=True)

    class Meta:
        unique_together = (('student', 'module_state_key', 'course_id'),)

    # Internal state of the object
    marketo_complete = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __repr__(self):
        return 'StudentModuleMarketo<%r>' % ({
            'course_id': self.course_id,
            'student': self.student.username,
            'module_state_key': self.module_state_key,
            'marketo_complete': self.marketo_complete,
        },)

    def __unicode__(self):
        return unicode(repr(self))
