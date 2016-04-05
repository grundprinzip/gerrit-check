# gerrit-check -- static code analysis to Gerrit comments

**TLDR: Turn cpplint / cppcheck / flake8 messages to Gerrit comments**

Many projects use Gerrit for code-reviews and in addition use static code 
analysis tools to report about the quality of the code in review. For example,
Jenkins comes with a nice integration of Gerrit, there is no suitable way to 
generate line-by-line annotations of the output of static code analysis tools 
for Gerrit.

This project allows you to transform the output of the tools: cppcheck, 
cpplint and flake8 into line by line comments in Gerrit.

## Installation

This is as easy as:

    sudo pip install gerrit-check
    
## Usage

The typical usage for this project is to use in conjunction with a continuous 
integration server that runs for example pre-commit checks on a particular 
Gerrit change set.

    gerrit-check -g gerrit.some.company.com \
        -t cpplint \
        --user jenkins \
        --commit ${GIT_HASH}
        
This will run cpplint on the modified files and lines identified by the 
*GIT_HASH* and submit a review on this patch to the Gerrit instance identified
in the arguments.

If access to the Gerrit server is not directly possible, the `-l` option will
force the output to be written to stdout so that it can be saved and 
post-processed.

In a similar way to the above described simplication the script could be used
as follows:

    gerrit-check -t cpplint --commit ${GIT_HASH} \
        | ssh jenkins@gerrit.some.company gerrit review ${GIT_HASH} --json
        
## License

Licensed under the Apache License, Version 2.0 (the "License"). You may not
use this file except in compliance with the License. A copy of the License
is located at: http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed
on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
express or implied. See the License for the specific language governing
permissions and limitations under the License.