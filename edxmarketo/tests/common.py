MICROSITE_CONFIG_ENABLED = {
    "default": {
        "course_enable_marketo_integration": True,
        "marketo_course_complete_field_map": {
            "testorg/101/marketo_test": "Course_1_Completed__c"
        },
        "marketo_course_access_field_map": {
            "testorg/101/marketo_test": "Course_1_Last_Access_Date__c"
        }
    }
}

MICROSITE_CONFIG_DISABLED = {
    "default": {
        "course_enable_marketo_integration": False,
    }
}
