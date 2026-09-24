"""Tests for ISS-05: handling branch changes before work starts."""

from __future__ import annotations

import subprocess
import pytest

from work_queue import (
    BranchMissingError,
    WorkItem,
    create_work,
    pr_base_for,
    start_work,
)


@pytest.fixture()
def repo(tmp_path):
    """A scratch git repository with an initial commit on main."""
    path = tmp_path / "repo"
    path.mkdir()
    def git(*args, check=True):
        return subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True, text=True, check=check,
        )
    git("init", "-q", "-b", "main")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test")
    (path / "file.txt").write_text("one\n")
    git("add", ".")
    git("commit", "-q", "-m", "initial")
    return path


def _commit(repo, message):
    (repo / "file.txt").write_text(message + "\n")
    subprocess.run(["git", "-C", str(repo), "commit", "-aqm", message], check=True)
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def test_missing_branch_at_submission_fails_without_creating_work(repo):
    subprocess.run(
        ["git", "-C", str(repo), "branch", "feature"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "branch", "-D", "feature"], check=True)
    with pytest.raises(BranchMissingError) as excinfo:
        create_work(str(repo), "feature", title="doomed")
    assert "feature" in str(excinfo.value)
    assert "not found" in str(excinfo.value)
    assert "falling back" in str(excinfo.value)


def test_renamed_branch_fails_at_submission(repo):
    subprocess.run(
        ["git", "-C", str(repo), "branch", "old-name"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "branch", "-m", "old-name", "new-name"],
        check=True,
    )
    with pytest.raises(BranchMissingError):
        create_work(str(repo), "old-name")
    # The renamed branch itself is still usable when selected explicitly.
    item = create_work(str(repo), "new-name")
    assert item.branch == "new-name"


def test_no_silent_fallback_to_default_branch(repo):
    with pytest.raises(BranchMissingError):
        create_work(str(repo), "does-not-exist")


def test_head_advanced_while_queued_uses_pinned_commit(repo):
    subprocess.run(["git", "-C", str(repo), "branch", "work"], check=True)
    work = create_work(str(repo), "work", title="queued")
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "work"], check=True)
    _commit(repo, "advance head")
    started = start_work(str(repo), work)
    assert started.head_advanced is True
    assert started.base_commit == work.base_commit
    assert started.base_commit != started.head_commit
    assert work.branch in started.describe()
    assert str(work.base_commit[:12]) in started.describe()


def test_head_advanced_rejected_when_disallowed(repo):
    subprocess.run(["git", "-C", str(repo), "branch", "strict"], check=True)
    work = create_work(str(repo), "strict")
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "strict"], check=True)
    _commit(repo, "advance")
    with pytest.raises(Exception) as excinfo:
        start_work(str(repo), work, allow_advanced_head=False)
    assert "advanced" in str(excinfo.value)


def test_branch_deleted_after_queueing_fails_at_start(repo):
    subprocess.run(["git", "-C", str(repo), "branch", "temp"], check=True)
    work = create_work(str(repo), "temp")
    subprocess.run(["git", "-C", str(repo), "branch", "-D", "temp"], check=True)
    with pytest.raises(BranchMissingError):
        start_work(str(repo), work)


def test_pr_base_matches_queued_branch_and_validates(repo):
    subprocess.run(["git", "-C", str(repo), "branch", "pr"], check=True)
    work = create_work(str(repo), "pr")
    assert pr_base_for(work, str(repo)) == "pr"
    subprocess.run(["git", "-C", str(repo), "branch", "-D", "pr"], check=True)
    with pytest.raises(BranchMissingError):
        pr_base_for(work, str(repo))
    assert pr_base_for(work) == "pr"


def test_head_unchanged_reports_not_advanced(repo):
    subprocess.run(["git", "-C", str(repo), "branch", "same"], check=True)
    work = create_work(str(repo), "same")
    started = start_work(str(repo), work)
    assert started.head_advanced is False
    assert started.base_commit == started.head_commit
