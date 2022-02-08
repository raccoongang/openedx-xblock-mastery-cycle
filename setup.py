"""Setup for mastery_cycle XBlock."""


import os

from setuptools import setup


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='mastery-cycle-xblock',
    version='0.0.1',
    description='Mastery Cycle XBlock',
    packages=[
        'mastery_cycle',
    ],
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': [
            'mastery_cycle = mastery_cycle:MasteryCycleXBlock',
        ],
        'openedx.block_structure_transformer': [
            'mastery_cycle = mastery_cycle:MasteryCycleTransformer',
        ]
    },
    package_data=package_data('mastery_cycle', ['static', 'public', 'translations']),
)
