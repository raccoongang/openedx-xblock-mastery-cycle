## Installation and configuration

After this, XBlock-mastery-cycle may be installed using its setup.py, or if you prefer to use pip, running:

    $ pip install git@gitlab.raccoongang.com:kraken/calypso-lilac/edx-xblock-mastery-cycle.git

You may specify the `-e` flag if you intend to develop on the repo.

### Setting up a course to use XBlock-mastery-cycle

To set up a course to use XBlock-mastery-cycle, first go to your course's outline page in the studio and look
for the Advanced settings link in the top menus.

Once there, look for the *Advanced Modules List* and add `"mastery_cycle"`.

Save your changes, and you may now add a xblock by clicking on the **Advanced Modules** button on the bottom of a
unit editing page and selecting `Mastery Cycle`.

#### Add in edx-platform

Change file `lms/djangoapps/course_blocks/api.py`

````
def get_course_block_access_transformers(user):
    
    course_block_access_transformers = [
        library_content.ContentLibraryTransformer(),
        library_content.ContentLibraryOrderTransformer(),
        start_date.StartDateTransformer(),
        ContentTypeGateTransformer(),
        user_partitions.UserPartitionTransformer(),
        visibility.VisibilityTransformer(),
        field_data.DateOverrideTransformer(user),
    ]

    if has_individual_student_override_provider():
        course_block_access_transformers += [load_override_data.OverrideDataTransformer(user)]

     if has_individual_student_override_provider():
         course_block_access_transformers += [load_override_data.OverrideDataTransformer(user)]

+    try:
+        from lms.djangoapps.courseware.field_overrides import resolve_dotted
+        course_block_access_transformers.insert(
+            0, resolve_dotted('mastery_cycle.MasteryCycleTransformer')()
+        )
+    except ModuleNotFoundError:
+        pass
+
     return course_block_access_transformers
````

### Description

#### Single Mastery Cycle Scenario 
If the student answers all mastery assessment questions correctly on the first pass  through the module, 
the student has met the mastery criteria and can advance to the  next module after having completed one mastery cycle. 
Since the order/position of the  assessment questions is different for each student, 
we can be confident that a student  who answers all questions correctly on the first pass has truly learned the material.

#### Multiple Mastery Cycle Scenarios 
During the first mastery cycle, if the student answers one or more questions incorrectly for a given assessment/quiz, 
the student has not met the mastery criteria and must subsequently go through at least one more mastery cycle 
and answer correctly twice all the assessment questions that weren’t mastered during the first pass before advancing to the next module.

- If the student answers correctly 50% or less of the questions presented within a module, that cycle is considered failed (anti-guess feature) and the student  must repeat the cycle and does not receive credit for that cycle
- If the student answers correctly more than 50% of the questions presented  within a module, the student may progress to the next cycle of that module;  however the student will subsequently be required to answer all questions that  he/she missed on that cycle. 
- If the student answers correctly 100% of the questions correctly for any given  assessment on the first pass, those questions are considered mastered and  the corresponding pages are not required to be reviewed during subsequent cycles.
