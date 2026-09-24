#!/usr/bin/env python3
'''Branch-aware work submission for the flight-tracker repository.

This module implements ISS-05: work items that reference a git branch must
be validated *before* the work is created, must pin the commit they are
based on when queued, and must never silently fall back to a different
branch when the selected one disappears (deleted or renamed).
'''

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional, Sequence


class BranchError(Exception):
    '''Base class for branch-related work submission errors.'''


class BranchMissingError(BranchError):
    '''Raised when the selected branch no longer exists (deleted or renamed).'''


@dataclass
class WorkItem:
    '''A queued unit of work pinned to a specific branch and commit.'''

    branch: str
    base_commit: str
    title: str = ''
    status: str = 'queued'

    @property
    def pr_base(self) -> str:
        '''The branch a pull request for this work will target.'''
        return self.branch


@dataclass
class WorkStart:
    '''Result of starting previously queued work.'''

    branch: str
    base_commit: str
    head_commit: str
    head_advanced: bool

    def describe(self) -> str:
        '''Human-readable explanation of the commit and PR base in use.'''
        lines = [
            f"Using pinned commit {self.base_commit[:12]} on branch "
            f"'{self.branch}' (queued base).",
        ]
        if self.head_advanced:
            lines.append(
                f"Branch head has advanced to {self.head_commit[:12]} since the "
                "work was queued; the queued base commit is used for the work "
                f"and '{self.branch}' remains the PR base."
            )
        else:
            lines.append(
                f"Branch head matches the queued commit ({self.head_commit[:12]})."
            )
        return '\n'.join(lines)


def _git(repo: str, args: Sequence[str]) -> str:
    result = subprocess.run(
        ['git', '-C', repo, *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise BranchError(
            f"git {' '.join(args)} failed in {repo!r}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def branch_exists(repo: str, branch: str) -> bool:
    '''Return True only when the exact branch ref exists in *repo*.'''
    result = subprocess.run(
        ['git', '-C', repo, 'rev-parse', '--verify', '--quiet',
         f'refs/heads/{branch}'],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def resolve_branch(repo: str, branch: str) -> str:
    '''Resolve *branch* to its current head commit.

    Raises :class:`BranchMissingError` when the branch does not exist. The
    error is explicit and actionable; the caller must never fall back to
    another branch (such as the default branch) on its own.
    '''
    if not branch or not isinstance(branch, str):
        raise BranchError('A branch name must be provided to create work.')
    if not branch_exists(repo, branch):
        raise BranchMissingError(
            f"Branch '{branch}' was not found in the repository. It may have "
            'been deleted or renamed since it was selected. Refusing to '
            'create work against a missing branch, and not falling back to '
            'any other branch. Re-select a valid branch and try again.'
        )
    return _git(repo, ['rev-parse', '--verify', f'refs/heads/{branch}^{{commit}}'])


def create_work(repo: str, branch: str, title: str = '') -> WorkItem:
    '''Validate the branch and queue work pinned to its current head commit.

    The branch is validated *before* any work is created so a deleted or
    renamed branch fails clearly instead of producing doomed work.
    '''
    base_commit = resolve_branch(repo, branch)
    return WorkItem(branch=branch, base_commit=base_commit, title=title)


def start_work(
    repo: str,
    work: WorkItem,
    allow_advanced_head: bool = True,
) -> WorkStart:
    '''Begin previously queued work.

    The branch is re-validated when the work starts. A branch that was
    deleted or renamed after queueing raises :class:`BranchMissingError`
    rather than silently rebasing onto another branch. If the branch head
    advanced while the work was queued, the pinned ``base_commit`` recorded
    at queue time is used (optionally rejected when
    *allow_advanced_head* is False) and the situation is reported plainly.
    '''
    current_head = resolve_branch(repo, work.branch)
    head_advanced = current_head != work.base_commit
    if head_advanced and not allow_advanced_head:
        raise BranchError(
            f"Branch '{work.branch}' has advanced from the queued commit "
            f"{work.base_commit[:12]} to {current_head[:12]} since the work "
            'was queued. Refusing to start on a moved branch.'
        )
    return WorkStart(
        branch=work.branch,
        base_commit=work.base_commit,
        head_commit=current_head,
        head_advanced=head_advanced,
    )


def pr_base_for(work: WorkItem, repo: Optional[str] = None) -> str:
    '''Return the PR base for *work*.

    The base is always the branch recorded when the work was queued. If the
    branch has since disappeared the error is explicit; there is no silent
    substitution of another branch.
    '''
    if repo is not None:
        resolve_branch(repo, work.branch)  # explicit failure if missing
    return work.pr_base
