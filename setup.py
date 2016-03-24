#!/usr/bin/env python
# Copyright 2016 Amazon.com, Inc. or its
# affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not
# use this file except in compliance with the License. A copy of the License
# is located at
#
#    http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

from setuptools import setup, find_packages

setup(name='gerrit-check',
      version='0.1',
      description='Line annotations for syntax checkers for Gerrit',
      author='Martin Grund',
      author_email='magrund@amazon.com',
      packages=find_packages(),
      install_requires=['plumbum', 'flake8', 'cpplint'],
      entry_points={
          'console_scripts': [
              'gerrit_check=gerritcheck.check:main'
          ]
      }
      )
