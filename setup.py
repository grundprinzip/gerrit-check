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
      version='0.1.1',
      description='Line annotations for syntax checkers for Gerrit',
      author='Martin Grund',
      author_email='grundprinzip@gmail.com',
      url="https://github.com/grundprinzip/gerrit-check",
      platforms=("Linux", ),
      long_description="""
Many projects use Gerrit for code-reviews and in addition use static code
analysis tools to report about the quality of the code in review. For example,
Jenkins comes with a nice integration of Gerrit, there is no suitable way to
generate line-by-line annotations of the output of static code analysis tools
for Gerrit.

This project allows you to transform the output of the tools: cppcheck,
cpplint and flake8 into line by line comments in Gerrit.
      """,
      license="Apache 2.0",
      packages=find_packages(),
      install_requires=['plumbum', 'flake8', 'cpplint'],
      entry_points={
          'console_scripts': [
              'gerrit-check=gerritcheck.check:main'
          ]
      }
      )
