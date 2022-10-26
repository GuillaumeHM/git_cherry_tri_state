#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "0.1"

import os
import argparse
import git
import re # regular expressions

default_title_strip_pattern = r"^\[.*\]\s*"

# Character used to print the ambiguous state of a commit
ambiguous_state_char='~'

# States that a commit can have, sorted by commit probability to be candidate for cherry-pick from min to
# max.
states = ('-', ambiguous_state_char, '+')

script_job = "Over layer to show ambiguous state by replacing '+' from git cherry output by '" \
        + ambiguous_state_char + "' if a commit title match is found on <upstream> branch. This " \
        "state means the commit exists in <upstream> with same title as in <reference> branch " \
        "but content differs."
arg_output_level_desc = "Output level : '-' all commits, '" + ambiguous_state_char + "' title " \
        "matched commits and content unmatched commits, '+' only content unmatched commits which " \
        "are candidate to cherry-pick on <upstream>. Default: " + states[0]
arg_title_stripper_desc = "Regular expression to strip commit titles before matching. " \
        "Default: %(default)s"
arg_upstream_desc = "Upstream branch where to search for content and titles matching."
arg_ref_branch_desc = "Reference branch where to list commits for which to compute a matching " \
        "state on upstream. Default: %(default)s"

script_job_additional = " Basically, git cherry only matches patch content between <upstream> "\
        "and <reference> branches and outputs result : +, patch content not matched, meaning " \
        "the commit is candidate to cherry-pick on <upstream>; -, patch content matched."


def cherry_tri_state(repo, upstream, branch, output_level=states[0], title_stripper=None):

    list_upstream_titles = []
    # Build list of comparable titles from commits on 'upstream' which aren't reachable from 'branch'
    for commit in repo.iter_commits(branch + ".." + upstream):
        commit_title = commit.message.splitlines()[0].rstrip()

        # Delete undesirable part of title to compare with
        if title_stripper:
            commit_title = title_stripper.sub('', commit_title, count=1)

        list_upstream_titles.append(commit_title)

    # Iterate cherry result list from 'branch' to push on 'upstream'
    for line in repo.git.cherry("-v", "--abbrev", upstream, branch).splitlines():
        state, sha1, title = line.split(None, 2)

        # If patch not found on upstream, search for a commit with same name
        if state == '+':
            compare_title = title

            # Delete undesirable part of title to compare with
            if title_stripper:
                compare_title = title_stripper.sub('', title, count=1)

            # Check commit title
            if compare_title in list_upstream_titles:
                state = ambiguous_state_char

        if states.index(state) >= states.index(output_level):
            print(state, sha1, title)

if __name__ == '__main__':

    # Set up argument parser and usage discourse
    arg_parser = argparse.ArgumentParser(description=script_job, epilog=script_job_additional)
    arg_parser.add_argument('-o', '--output_level', dest='output_level', metavar='output-level',
            default=states[0], choices=states, type=str, help=arg_output_level_desc)
    arg_parser.add_argument('-s', '--strip_title', dest='strip_title', metavar='strip-title',
            default=default_title_strip_pattern, type=str, help=arg_title_stripper_desc)
    arg_parser.add_argument(dest='upstream', metavar='upstream-branch', type=str, help=arg_upstream_desc)
    arg_parser.add_argument(dest='branch', metavar='reference-branch', default="HEAD", nargs='?',
            type=str, help=arg_ref_branch_desc)
    args = arg_parser.parse_args()

    repo = git.Repo("./")
    cherry_tri_state(repo, args.upstream, args.branch, args.output_level, \
            re.compile(args.strip_title) if args.strip_title else None)
