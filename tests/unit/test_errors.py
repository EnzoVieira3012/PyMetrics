"""Unit tests for custom exceptions."""

from core.errors import GithubClientError


def test_github_client_error_is_exception():
    assert issubclass(GithubClientError, Exception)


def test_github_client_error_message():
    err = GithubClientError("erro amigável")
    assert str(err) == "erro amigável"
