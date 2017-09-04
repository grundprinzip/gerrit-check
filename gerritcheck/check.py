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
from __future__ import absolute_import, print_function

from collections import defaultdict
from plumbum import local, SshMachine
from flake8.api.legacy import get_style_guide

# Subprocess is used to address https://github.com/tomerfiliba/plumbum/issues/295
from subprocess import Popen, PIPE
import argparse
try:
    from exceptions import RuntimeError
except:
    # In Python3 all exceptions are built-in
    pass
import json
import multiprocessing
import os
import sys



CPP_HEADER_FILES = (".h", ".hpp")
CPP_SOURCE_FILES = (".c", ".cc", ".cpp")
CPP_FILES = CPP_HEADER_FILES + CPP_SOURCE_FILES

# Default cpplint options that are passed on during the execution
DEFAULT_CPPLINT_FILTER_OPTIONS=("-legal/copyright", "-build/include_order")

# Prepare global git cmd
git = local["git"]

class GerritCheckExecption(RuntimeError):
    pass

def extract_files_for_commit(rev):
    """
    :return: A list of files that where modified in revision 'rev'
    """
    diff = Popen(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", str(rev)],
            stdout=PIPE)

    out, err = diff.communicate()

    if err:
        raise GerritCheckExecption("Could not run diff on current revision. "
                                   "Make sure that the current revision has a "
                                   "parent:" + err)
    return [f.strip() for f in out.splitlines() if len(f)]


def filter_files(files, suffix=CPP_FILES):
    result = []
    for f in files:
        if f.endswith(suffix) and os.path.exists(f):
            result.append(f)
    return result


def line_part_of_commit(file, line, commit):
    """Helper function that returns true if a particular `line` in a
    particular `file` was last changed in `commit`."""
    line_val = git("blame", "-l", "-L{0},{0}".format(line), file)
    return line_val.split(" ", 1)[0] == commit


def flake8_on_files(files, commit):
    """ Runs flake8 on the files to report style guide violations.
    """
    style = get_style_guide(config_file=None, quiet=False)

    # We need to redirect stdout while generating the JSON to avoid spilling
    # messages to the user.
    old_stdout = sys.stdout
    sys.stdout = open("/dev/null", "w")
    review = {}
    for file in filter_files(files, (".py", )):
        report = style.check_files((file, ))
        if report.total_errors:
            if not "comments" in review:
                review["comments"] = defaultdict(list)
            for line_number, offset, code, text, doc in report._deferred_print:
                if not line_part_of_commit(file, line_number, commit): continue
                review["comments"][file].append({
                "path": file,
                "line": line_number,
                "message": "[{0}] {1}".format(code, text)
            })
    if "comments" in review and len(review["comments"]):
        review["message"] = "[FLAKE8] Some issues found."
    else:
        review["message"] = "[FLAKE8] No issues found. OK"
    sys.stdout = old_stdout
    return json.dumps(review)


def cppcheck_on_files(files, commit):
    """ Runs cppcheck on a list of input files changed in `commit` and
    returns a JSON structure in the format required for Gerrit
    to submit a review.
    """
    cppcheck_cmd = local["cppcheck"][
        "--quiet",
        "-j %d" % (multiprocessing.cpu_count() * 2),
        "--template={file}###{line}###{severity}###{message}"]

    # Each line in the output is an issue
    review = {}
    _, _, err = cppcheck_cmd.run(filter_files(files, CPP_SOURCE_FILES),
                                 retcode=None)
    if len(err) > 0:
        review["message"] = "[CPPCHECK] Some issues need to be fixed."

        review["comments"] = defaultdict(list)
        for c in err.split("\n"):
            if len(c.strip()) == 0: continue

            parts = c.split("###")

            # Only add a comment if code was changed in the modified region
            if not line_part_of_commit(parts[0], parts[1], commit): continue

            review["comments"][parts[0]].append({
                "path": parts[0],
                "line": parts[1],
                "message": "[{0}] {1}".format(parts[2], parts[3])
            })

        if len(review["comments"]):
            review["labels"] = {"Code-Review": -1}
            return json.dumps(review)

    # Add a review comment that no issues have been found
    review["message"] = "[CPPCHECK] No issues found. OK"
    return json.dumps(review)


def cpplint_on_files(files, commit, filters=DEFAULT_CPPLINT_FILTER_OPTIONS):
    """  Runs cpplint on a list of input files changed in `commit` and
    returns a JSON structure in the format required for Gerrit
    to submit a review.
    """
    cpplint_cmd = local["cpplint"]["--filter={0}".format(",".join(filters))]

    # Each line in the output is an issue
    review = {}
    _, _, err = cpplint_cmd.run(filter(os.path.exists, files), retcode=None)
    if len(err) > 0 and len(files):
        review["message"] = "[CPPLINT] Some issues need to be fixed."
        review["comments"] = defaultdict(list)
        for c in err.split("\n"):
            if len(c.strip()) == 0 or c.strip().startswith("Done") or \
                    c.strip().startswith("Total") or \
                    c.strip().startswith("Ignoring"): continue

            # cpplint cannot be configured to output a custom format so we
            # rely on knowing that the individual components are
            # two-space separated.
            location, rest = c.split("  ", 1)
            message, category = rest.rsplit("  ", 1)
            file, line, _ = location.split(":", 2)

            # Only add a comment if code was changed in the modified region
            if not line_part_of_commit(file, line, commit): continue
            review["comments"][file].append({
                "path": file,
                "line": line,
                "message": "[{0}] {1}".format(category, message)
            })
        if len(review["comments"]):
            review["labels"] = {"Code-Review": -1}
            return json.dumps(review)

    # Add a review comment that no issues have been found
    review["message"] = "[CPPLINT] No issues found. OK"
    return json.dumps(review)


def submit_review(change, user, host, data, port=22):
    """Uses the data as input to submit a new review."""
    remote = local["ssh"]["{0}@{1}:{2}".format(user, host, port)]
    (local["cat"] << data | remote["gerrit", "review", change, "--json"])()



# Mapping a particular checking function to a tool name
CHECKER_MAPPING = {
    "cppcheck": cppcheck_on_files,
    "cpplint": cpplint_on_files,
    "flake8": flake8_on_files
}

def main():
    parser = argparse.ArgumentParser(
            description=("Execute code analysis and report results locally "
                         "or to gerrit"),
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-g", "--gerrit-host", help="Gerrit host")
    parser.add_argument("-u", "--user", help="Username", default="jenkins")
    parser.add_argument("-p", "--port", help="SSH port Gerrit listens on",
                        default=22)
    parser.add_argument("-c", "--commit",
                        help="Git Hash of the commit to check",
                        default="HEAD")
    parser.add_argument("-t", "--tool", help="Which validation to run",
                        choices=CHECKER_MAPPING.keys(), action="append",
                        required=True)
    parser.add_argument("-l", "--local", action="store_true", default=False,
                        help=("Display output locally instead "
                              "of submitting it to Gerrit"))

    args = parser.parse_args()

    # If commit is set to HEAD, no need to backup the previous revision
    if args.commit != "HEAD":
        hash_before = local["git"]("rev-parse", "HEAD").strip()
        local["git"]("checkout", args.commit)

    modified_files = extract_files_for_commit(args.commit)

    current_hash = local["git"]("rev-parse", args.commit).strip()
    for t in args.tool:
        result = CHECKER_MAPPING[t](modified_files, current_hash)
        if args.local:
            print (json.dumps(json.loads(result)))
        else:
            submit_review(args.commit, args.user,
                          args.gerrit_host, result, args.port)

    # Only need to revert to previous change if the commit is
    # different from HEAD
    if args.commit != "HEAD":
        git("checkout", hash_before)

if __name__ == "__main__":
    main()
