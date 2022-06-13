import logging
import pkg_resources
import random
from copy import copy
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from opaque_keys.edx.locator import BlockUsageLocator
from openedx.core.lib.gating.api import get_required_content
from six import text_type
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Integer, Scope, String, Float, List, Boolean
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin, StudioContainerXBlockMixin
from xmodule.validation import StudioValidation, StudioValidationMessage

from lms.djangoapps.instructor.enrollment import reset_student_attempts

from xmodule.x_module import STUDENT_VIEW
from .utils import _

loader = ResourceLoader(__name__)
log = logging.getLogger(__name__)


@XBlock.needs('user')
@XBlock.needs('i18n')
class MasteryCycleXBlock(StudioEditableXBlockMixin, StudioContainerXBlockMixin, XBlock):
    display_name = String(
        display_name=_('Display Name'),
        help=_('The display name for this "Mastery Cycle" problem.'),
        scope=Scope.settings,
        default=_('Mastery Cycle'),
    )

    max_count = Integer(
        display_name=_("Count"),
        help=_("Enter the number of problems to display to each student."),
        default=5,
        scope=Scope.settings,
    )

    weight = Float(
        display_name=_('Problem Weight'),
        help=_('Defines the number of points the problem is worth.'),
        scope=Scope.settings,
        default=1,
    )

    selected = List(default=[], scope=Scope.user_state)
    incorrect = List(default=[], scope=Scope.user_state)
    half_mastered = List(default=[], scope=Scope.user_state)
    mastered = List(default=[], scope=Scope.user_state)
    pass_count = Integer(default=0, scope=Scope.user_state)
    done = Boolean(default=False, scope=Scope.user_state)

    has_children = True
    has_score = True
    icon_class = 'problem'
    show_in_read_only_mode = True
    editable_fields = ('display_name', 'max_count', )

    def author_edit_view(self, context):
        """
        Child blocks can override this to control the view shown to authors in Studio when
        editing this block's children.
        """
        fragment = Fragment()
        self.render_children(context, fragment, can_reorder=True, can_add=True)
        fragment.add_css(self.resource_string('static/css/mastery_cycle_author_edit.css'))
        return fragment

    def author_preview_view(self, context):
        """
        Child blocks can override this to add a custom preview shown to authors in Studio when
        not editing this block's children.
        """
        return Fragment()

    def student_view(self, context):
        fragment = Fragment()
        contents = []
        child_context = {} if not context else copy(context)

        if not self.done:
            for child in self._get_selected_child_blocks():
                if child is None:
                    # This shouldn't be happening, but does for an as-of-now
                    # unknown reason. Until we address the underlying issue,
                    # let's at least log the error explicitly, ignore the
                    # exception, and prevent the page from resulting in a
                    # 500-response.
                    log.error('Skipping display for child block that is None')
                    continue

                for displayable in child.displayable_items():
                    rendered_child = displayable.render(STUDENT_VIEW, child_context)
                    fragment.add_fragment_resources(rendered_child)
                    contents.append({
                        'id': text_type(displayable.location),
                        'content': rendered_child.content,
                    })

            fragment.add_content(loader.render_django_template(
                'static/html/state.html',
                {'length': len(contents)}
            ))

            fragment.add_content(self.system.render_template('vert_module.html', {
                'items': contents,
                'xblock_context': context,
                'show_bookmark_button': False,
                'watched_completable_blocks': set(),
                'completion_delay_ms': None,
            }))

        fragment.add_content(loader.render_django_template(
            'static/html/mastery_cycle.html',
            {'done': self.done},
            i18n_service=self.runtime.service(self, 'i18n')
        ))
        fragment.add_javascript(self.resource_string('static/js/src/mastery_cycle.js'))
        fragment.initialize_js('MasteryCycleXBlock')

        return fragment

    @XBlock.json_handler
    def check_problems(self, data, suffix=''):
        if not self.selected:
            return {
                'status': 'error',
                'msg': _('An error has occurred. Reload the page.'),
                'button_text': _('Reload'),
                'url': ''
            }

        attempted_answers, correct_answers, incorrect_answers = self.review_answers()

        if attempted_answers != len(self.selected):
            return {
                'status': 'not_all_answered',
                'msg': _('Not all problems answered.'),
                'button_text': _('Continue'),
            }

        user = self.runtime.service(self, "user")._django_user
        self.save_student_data(correct_answers, incorrect_answers)
        self.reset_student_problems(user)

        if len(self.mastered) >= self.max_count:
            self.publish_grade()
            self.done = True
            return {
                'status': 'done',
                'msg': _("You're doing great! Keep up the good work!"),
                'button_text': _('Next'),
            }

        button_text = _('Continue')
        url = ''

        if self.pass_count == 1:
            button_text, url = self.reset_student_prerequisite(user)

        return {
            'status': 'not_done',
            'msg': _("Let's review what we've learned a bit more. Please try again."),
            'button_text': button_text,
            'url': url
        }

    def review_answers(self):
        attempted_answers = 0
        correct_answers = set()
        incorrect_answers = set()

        for block_type, block_id in self.selected:
            problem = self.runtime.get_block(self.location.course_key.make_usage_key(block_type, block_id))
            attempted_answers += 1 if problem.is_attempted() else 0

            if problem.is_correct():
                correct_answers.add((block_type, block_id))
            else:
                incorrect_answers.add((block_type, block_id))

        return attempted_answers, correct_answers, incorrect_answers

    def save_student_data(self, correct_answers, incorrect_answers):
        mastered = {tuple(k) for k in self.mastered}
        half_mastered = {tuple(k) for k in self.half_mastered}
        incorrect = {tuple(k) for k in self.incorrect}

        percent_problems_correct = len(correct_answers) * 100 / len(self.selected)

        if percent_problems_correct > 50:
            if self.pass_count == 0:
                mastered = correct_answers
                incorrect = incorrect_answers
            else:
                mastered |= half_mastered.intersection(correct_answers)  # answered correctly twice
                half_mastered = half_mastered.symmetric_difference(correct_answers) - mastered  # answered correctly once
                incorrect |= incorrect_answers
                incorrect = incorrect.difference(mastered, half_mastered)
        else:
            incorrect |= incorrect_answers
            incorrect |= correct_answers
            incorrect = incorrect.difference(mastered, half_mastered)

        self.mastered = list(mastered)
        self.half_mastered = list(half_mastered)
        self.incorrect = list(incorrect)
        self.pass_count += 1

    def reset_student_problems(self, user):
        for block_type, block_id in self.selected:
            problem = self.runtime.get_block(self.location.course_key.make_usage_key(block_type, block_id))
            try:
                reset_student_attempts(self.location.course_key, user, problem.location, user, delete_module=True)
            except ObjectDoesNotExist:
                pass
        self.selected = []

    def reset_student_prerequisite(self, user):
        button_text = _('Continue')
        url = ''
        prerequisite_usage_key, __, __ = get_required_content(
            self.location.course_key,
            self.get_parent().get_parent().location  # current subsection
        )
        if prerequisite_usage_key:
            prerequisite_usage_key = BlockUsageLocator.from_string(prerequisite_usage_key)

            try:
                reset_student_attempts(self.location.course_key, user, prerequisite_usage_key, user, delete_module=True)
            except ObjectDoesNotExist:
                pass

            button_text = _('Review the material')
            url = reverse(
                'jump_to',
                kwargs={
                    'course_id': self.location.course_key,
                    'location': text_type(prerequisite_usage_key),
                }
            )
        return button_text, url

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def publish_grade(self):
        self.runtime.publish(
            self,
            'grade',
            {
                'value': self.weight,
                'max_value': self.weight,
            })

    def max_score(self):
        """
        Return the maximum score possible.
        """
        return self.weight

    def _get_selected_child_blocks(self):
        """
        Generator returning XBlock instances of the children selected for the
        current user.
        """
        for block_type, block_id in self.selected_children():
            yield self.runtime.get_block(self.location.course_key.make_usage_key(block_type, block_id))

    def selected_children(self):
        """
        Returns a list() of block_ids indicating which of the possible children
        have been selected to display to the current user.

        This reads and updates the "selected" field, which has user_state scope.
        """

        block_keys = self.make_selection(
            self.selected, self.incorrect, self.half_mastered, self.mastered, self.children, self.max_count
        )

        if any(block_keys[changed] for changed in ('invalid', 'overlimit', 'added')):
            # Save our selections to the user state, to ensure consistency:
            selected = block_keys['selected']
            self.selected = selected

        return self.selected

    @classmethod
    def make_selection(cls, selected, incorrect, half_mastered, mastered, children, max_count):
        """
        Dynamically selects block_ids indicating which of the possible children are displayed to the current user.
        """
        rand = random.Random()

        selected_keys = {tuple(k) for k in selected}  # set of (block_type, block_id) tuples assigned to this student
        incorrect_keys = {tuple(k) for k in incorrect}
        half_mastered_keys = {tuple(k) for k in half_mastered}
        mastered_keys = {tuple(k) for k in mastered}

        # Determine which of our children we will show:
        valid_block_keys = {(c.block_type, c.block_id) for c in children}

        # Remove any selected blocks that are no longer valid:
        invalid_block_keys = (selected_keys - valid_block_keys)
        if invalid_block_keys:
            selected_keys -= invalid_block_keys

        # If max_count has been decreased, we may have to drop some previously selected blocks:
        overlimit_block_keys = set()
        if len(selected_keys) > max_count:
            num_to_remove = len(selected_keys) - max_count
            overlimit_block_keys = set(rand.sample(selected_keys, num_to_remove))
            selected_keys -= overlimit_block_keys

        incorrect_keys = incorrect_keys.intersection(valid_block_keys)
        half_mastered_keys = half_mastered_keys.intersection(valid_block_keys)
        mastered_keys = mastered_keys.intersection(valid_block_keys)

        # Do we have enough blocks now?
        num_to_add = max_count - len(selected_keys)
        added_block_keys = set()

        # priority: incorrect, half_mastered, mastered, questions_left
        for position, priority_keys in enumerate([incorrect_keys, half_mastered_keys, mastered_keys, valid_block_keys]):

            if num_to_add <= 0:
                break

            if position == 3:  # questions_left
                priority_keys = priority_keys - mastered_keys

            priority_keys = priority_keys - selected_keys
            added_block_keys = set(rand.sample(priority_keys, min(len(priority_keys), num_to_add)))
            selected_keys |= added_block_keys
            num_to_add = max_count - len(selected_keys)

        if any((invalid_block_keys, overlimit_block_keys, added_block_keys)):
            selected = list(selected_keys)
            random.shuffle(selected)

        return {
            'selected': selected,
            'invalid': invalid_block_keys,
            'overlimit': overlimit_block_keys,
            'added': added_block_keys,
        }

    def validate(self):
        """
        Validates the state of this Mastery Cycle Instance.
        """

        validation = super().validate()

        if not isinstance(validation, StudioValidation):
            validation = StudioValidation.copy(validation)

        children_count = len(self.children)

        if children_count < self.max_count:
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.WARNING,
                    _(
                        'Сonfigured number of problems to display to each student - {count}, '
                        'but there is only {actual}.'
                    ).format(count=self.max_count, actual=children_count),
                )
            )

        return validation
