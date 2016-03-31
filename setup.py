# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="shine",
    version='0.1.37',
    zip_safe=False,
    platforms='any',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    scripts=['shine/bin/shine'],
    install_requires=['events', 'pyzmq', 'netkit', 'click', 'setproctitle', 'redis'],
    url="https://github.com/dantezhu/shine",
    license="MIT",
    author="dantezhu",
    author_email="zny2008@gmail.com",
    description="shine",
)
