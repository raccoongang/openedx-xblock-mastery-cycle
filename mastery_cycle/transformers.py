from openedx.core.djangoapps.content.block_structure.transformer import (
    BlockStructureTransformer,
    FilteringTransformerMixin
)


class MasteryCycleTransformer(FilteringTransformerMixin, BlockStructureTransformer):
    """
    A transformer that manipulates the block structure
    by removing all blocks within a mastery_cycle module,
    because they do not need to be included in the grade.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls):
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py.
        """
        return "mastery_cycle"

    def transform_block_filters(self, usage_info, block_structure):
        mastery_cycle_children = set()
        for block_key in block_structure:
            if block_key.block_type == 'mastery_cycle':
                children = block_structure.get_children(block_key)

                if children:
                    mastery_cycle_children.update(children)

        def check_child_removal(block_key):
            """
            Return True if selected block should be removed.
            Block is removed if it is part of mastery_cycle.
            """
            return block_key in mastery_cycle_children

        return [block_structure.create_removal_filter(check_child_removal)]
