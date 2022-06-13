# -*- coding: utf-8 -*-
import mock
import unittest

from xblock.field_data import DictFieldData
from mastery_cycle import MasteryCycleXBlock


class MasteryCycleXBlockTests(unittest.TestCase):

    def make_one(self, **kw):
        """
        Creates a MasteryCycleXBlock for testing purpose.
        """
        field_data = DictFieldData(kw)
        runtime = kw.pop('runtime', mock.Mock())

        block = MasteryCycleXBlock(runtime, field_data, mock.Mock())
        block.location = mock.Mock(
            block_id='block_id',
            org='org',
            course='course',
            block_type='mastery_cycle'
        )
        return block

    def test_save_student_data_when_50_percent_not_scored_on_first_pass(self):
        # arrange:
        xblock = self.make_one()
        xblock.selected = [['problem', '1'], ['problem', '2'], ['problem', '3'], ['problem', '4'], ['problem', '5']]
        correct_answers = {('problem', '1'), ('problem', '2')}
        incorrect_answers = {('problem', '3'), ('problem', '4'), ('problem', '5')}

        # act:
        xblock.save_student_data(correct_answers, incorrect_answers)

        # assert:
        self.assertListEqual(xblock.mastered, [])
        self.assertListEqual(xblock.half_mastered, [])
        self.assertSetEqual(
            set(xblock.incorrect),
            {('problem', '1'), ('problem', '2'), ('problem', '3'), ('problem', '4'), ('problem', '5')}
        )
        self.assertEqual(xblock.pass_count, 1)

    def test_save_student_data_when_50_percent_scored_on_first_pass(self):
        # arrange:
        xblock = self.make_one()
        xblock.selected = [['problem', '1'], ['problem', '2'], ['problem', '3'], ['problem', '4'], ['problem', '5']]
        correct_answers = {('problem', '1'), ('problem', '2'), ('problem', '3')}
        incorrect_answers = {('problem', '4'), ('problem', '5')}

        # act:
        xblock.save_student_data(correct_answers, incorrect_answers)

        # assert:
        self.assertSetEqual(
            set(xblock.mastered),
            {('problem', '1'), ('problem', '2'), ('problem', '3')}
        )
        self.assertListEqual(xblock.half_mastered, [])
        self.assertSetEqual(
            set(xblock.incorrect),
            {('problem', '4'), ('problem', '5')}
        )
        self.assertEqual(xblock.pass_count, 1)

    def test_save_student_data_when_100_percent_scored_on_first_pass(self):
        # arrange:
        xblock = self.make_one()
        xblock.selected = [['problem', '1'], ['problem', '2'], ['problem', '3'], ['problem', '4'], ['problem', '5']]
        correct_answers = {('problem', '1'), ('problem', '2'), ('problem', '3'), ('problem', '4'), ('problem', '5')}
        incorrect_answers = set()

        # act:
        xblock.save_student_data(correct_answers, incorrect_answers)

        # assert:
        self.assertSetEqual(
            set(xblock.mastered),
            {('problem', '1'), ('problem', '2'), ('problem', '3'), ('problem', '4'), ('problem', '5')}
        )
        self.assertListEqual(xblock.half_mastered, [])
        self.assertListEqual(xblock.incorrect, [])
        self.assertEqual(xblock.pass_count, 1)

    def test_save_student_data_when_50_percent_not_scored_on_next_pass(self):
        # arrange:
        xblock = self.make_one()
        xblock.pass_count = 1
        xblock.mastered = [('problem', '3')]
        xblock.half_mastered = [('problem', '4')]
        xblock.incorrect = [('problem', '2'), ('problem', '6')]
        xblock.selected = [['problem', '1'], ['problem', '2'], ['problem', '3'], ['problem', '4'], ['problem', '5']]

        correct_answers = {('problem', '1'), ('problem', '2')}
        incorrect_answers = {('problem', '3'), ('problem', '4'), ('problem', '5')}

        # act:
        xblock.save_student_data(correct_answers, incorrect_answers)

        # assert:
        self.assertSetEqual(
            set(xblock.mastered),
            {('problem', '3')}
        )
        self.assertSetEqual(
            set(xblock.half_mastered),
            {('problem', '4')}
        )
        self.assertSetEqual(
            set(xblock.incorrect),
            {('problem', '1'), ('problem', '2'), ('problem', '5'), ('problem', '6')}
        )
        self.assertEqual(xblock.pass_count, 2)

    def test_save_student_data_when_50_percent_scored_on_next_pass(self):
        # arrange:
        xblock = self.make_one()
        xblock.pass_count = 1
        xblock.mastered = [('problem', '3')]
        xblock.half_mastered = [('problem', '4')]
        xblock.incorrect = [('problem', '1'), ('problem', '2')]
        xblock.selected = [['problem', '1'], ['problem', '2'], ['problem', '3'], ['problem', '4'], ['problem', '5']]

        correct_answers = {('problem', '1'), ('problem', '2'), ('problem', '4')}
        incorrect_answers = {('problem', '5'), ('problem', '3')}

        # act:
        xblock.save_student_data(correct_answers, incorrect_answers)

        # assert:
        self.assertSetEqual(
            set(xblock.mastered),
            {('problem', '3'), ('problem', '4')}
        )
        self.assertSetEqual(
            set(xblock.half_mastered),
            {('problem', '1'), ('problem', '2')}
        )
        self.assertSetEqual(
            set(xblock.incorrect),
            {('problem', '5')}
        )
        self.assertEqual(xblock.pass_count, 2)

    def test_save_student_data_when_100_percent_scored_on_next_pass(self):
        # arrange:
        xblock = self.make_one()
        xblock.pass_count = 1
        xblock.mastered = [('problem', '3')]
        xblock.half_mastered = [('problem', '4')]
        xblock.incorrect = [('problem', '1'), ('problem', '2')]
        xblock.selected = [['problem', '1'], ['problem', '2'], ['problem', '3'], ['problem', '4'], ['problem', '5']]

        correct_answers = {('problem', '1'), ('problem', '2'), ('problem', '3'), ('problem', '4'), ('problem', '5')}
        incorrect_answers = set()

        # act:
        xblock.save_student_data(correct_answers, incorrect_answers)

        # assert:
        self.assertSetEqual(
            set(xblock.mastered),
            {('problem', '3'), ('problem', '4')}
        )
        self.assertSetEqual(
            set(xblock.half_mastered),
            {('problem', '1'), ('problem', '2'), ('problem', '5')}
        )
        self.assertListEqual(xblock.incorrect, [])
        self.assertEqual(xblock.pass_count, 2)

    def test_make_selection_when_empty_incorrect_and_half_mastered_and_mastered(self):
        # arrange:
        selected = []
        incorrect = []
        half_mastered = []
        mastered = []
        children = [
            mock.Mock(block_type='problem', block_id=1),
            mock.Mock(block_type='problem', block_id=2),
            mock.Mock(block_type='problem', block_id=3),
            mock.Mock(block_type='problem', block_id=4),
            mock.Mock(block_type='problem', block_id=5),
            mock.Mock(block_type='problem', block_id=6),
            mock.Mock(block_type='problem', block_id=7),
        ]
        max_count = 5

        # act:
        result = MasteryCycleXBlock.make_selection(selected, incorrect, half_mastered, mastered, children, max_count)

        # assert:
        self.assertEqual(len(result['selected']), 5)
        self.assertEqual(len(result['invalid']), 0)
        self.assertEqual(len(result['overlimit']), 0)
        self.assertEqual(len(result['added']), 5)

    def test_make_selection_when_empty_half_mastered_and_empty_mastered_and_exist_incorrect(self):
        # arrange:
        selected = []
        mastered = []
        half_mastered = []
        incorrect = [
            ['problem', 1],
            ['problem', 2],
        ]
        children = [
            mock.Mock(block_type='problem', block_id=1),
            mock.Mock(block_type='problem', block_id=2),
            mock.Mock(block_type='problem', block_id=3),
            mock.Mock(block_type='problem', block_id=4),
            mock.Mock(block_type='problem', block_id=5),
            mock.Mock(block_type='problem', block_id=6),
            mock.Mock(block_type='problem', block_id=7),
        ]
        max_count = 5

        # act:
        result = MasteryCycleXBlock.make_selection(selected, incorrect, half_mastered, mastered, children, max_count)

        # assert:
        self.assertEqual(len(result['selected']), 5)
        self.assertIn(('problem', 1), result['selected'])
        self.assertIn(('problem', 2), result['selected'])
        self.assertEqual(len(result['invalid']), 0)
        self.assertEqual(len(result['overlimit']), 0)
        self.assertEqual(len(result['added']), 3)

    def test_make_selection_when_empty_mastered_and_exist_incorrect_and_exist_half_mastered(self):
        # arrange:
        selected = []
        mastered = []
        half_mastered = [
            ['problem', 3],
            ['problem', 4],
            ['problem', 5],
        ]
        incorrect = [
            ['problem', 6],
            ['problem', 7],
        ]
        children = [
            mock.Mock(block_type='problem', block_id=1),
            mock.Mock(block_type='problem', block_id=2),
            mock.Mock(block_type='problem', block_id=3),
            mock.Mock(block_type='problem', block_id=4),
            mock.Mock(block_type='problem', block_id=5),
            mock.Mock(block_type='problem', block_id=6),
            mock.Mock(block_type='problem', block_id=7),
        ]
        max_count = 5

        # act:
        result = MasteryCycleXBlock.make_selection(selected, incorrect, half_mastered, mastered, children, max_count)

        # assert:
        self.assertEqual(len(result['selected']), 5)
        self.assertIn(('problem', 3), result['selected'])
        self.assertIn(('problem', 4), result['selected'])
        self.assertIn(('problem', 5), result['selected'])
        self.assertIn(('problem', 6), result['selected'])
        self.assertIn(('problem', 7), result['selected'])
        self.assertEqual(len(result['invalid']), 0)
        self.assertEqual(len(result['overlimit']), 0)
        self.assertEqual(len(result['added']), 3)

    def test_make_selection_when_exist_incorrect_and_half_mastered_and_mastered(self):
        # arrange:
        selected = []
        mastered = [
            ['problem', 5],
        ]
        half_mastered = [
            ['problem', 1],
            ['problem', 2],
            ['problem', 3],
        ]
        incorrect = [
            ['problem', 4],
        ]
        children = [
            mock.Mock(block_type='problem', block_id=1),
            mock.Mock(block_type='problem', block_id=2),
            mock.Mock(block_type='problem', block_id=3),
            mock.Mock(block_type='problem', block_id=4),
            mock.Mock(block_type='problem', block_id=5),
            mock.Mock(block_type='problem', block_id=6),
            mock.Mock(block_type='problem', block_id=7),
        ]
        max_count = 5

        # act:
        result = MasteryCycleXBlock.make_selection(selected, incorrect, half_mastered, mastered, children, max_count)

        # assert:
        self.assertEqual(len(result['selected']), 5)
        self.assertIn(('problem', 1), result['selected'])
        self.assertIn(('problem', 2), result['selected'])
        self.assertIn(('problem', 3), result['selected'])
        self.assertIn(('problem', 4), result['selected'])
        self.assertIn(('problem', 5), result['selected'])
        self.assertNotIn(('problem', 6), result['selected'])
        self.assertNotIn(('problem', 7), result['selected'])
        self.assertEqual(len(result['invalid']), 0)
        self.assertEqual(len(result['overlimit']), 0)
        self.assertEqual(len(result['added']), 1)

    def test_make_selection_when_exist_incorrect_and_exist_mastered_and_empty_half_mastered(self):
        # arrange:
        selected = []
        mastered = [
            ['problem', 5],
            ['problem', 1],
            ['problem', 2],
            ['problem', 3],
        ]
        half_mastered = []
        incorrect = [
            ['problem', 4],
        ]
        children = [
            mock.Mock(block_type='problem', block_id=1),
            mock.Mock(block_type='problem', block_id=2),
            mock.Mock(block_type='problem', block_id=3),
            mock.Mock(block_type='problem', block_id=4),
            mock.Mock(block_type='problem', block_id=5),
            mock.Mock(block_type='problem', block_id=6),
            mock.Mock(block_type='problem', block_id=7),
        ]
        max_count = 5

        # act:
        result = MasteryCycleXBlock.make_selection(selected, incorrect, half_mastered, mastered, children, max_count)

        # assert:
        self.assertEqual(len(result['selected']), 5)
        self.assertIn(('problem', 1), result['selected'])
        self.assertIn(('problem', 2), result['selected'])
        self.assertIn(('problem', 3), result['selected'])
        self.assertIn(('problem', 4), result['selected'])
        self.assertIn(('problem', 5), result['selected'])
        self.assertNotIn(('problem', 6), result['selected'])
        self.assertNotIn(('problem', 7), result['selected'])
        self.assertEqual(len(result['invalid']), 0)
        self.assertEqual(len(result['overlimit']), 0)
        self.assertEqual(len(result['added']), 4)
