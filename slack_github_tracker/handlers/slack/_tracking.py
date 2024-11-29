from typing import Self
from urllib import parse

import attrs

from . import _interpret as interpret


@attrs.define
class InvalidPR(interpret.CommandError):
    command: str

    def __str__(self) -> str:
        return f"Please provide one argument to {self.command} as a url that is either `github.com/<organisation>/<repo>/pull/<pr_number>` or `<organisation>/<repo>/pull/<pr_number>`"


@attrs.frozen
class PR:
    organisation: str
    repo: str
    pr_number: int

    @property
    def display(self) -> str:
        return f"PR#{self.pr_number} in {self.organisation}/{self.repo}"


@attrs.frozen
class TrackPRMessage(interpret.CommandMessage):
    pr_to_track: PR

    @classmethod
    def deserialize(cls, message: dict[str, object]) -> Self:
        message = dict(message)
        if not (text := message.get("text")) or not isinstance(text, str):
            raise ValueError("Expected 'text' in the body")

        if not (command := message.get("command")) or not isinstance(command, str):
            raise ValueError("Expected 'command' in the body")

        while text and text.startswith("/"):
            text = text[1:]

        url = parse.urlparse(text)

        if url.netloc not in ("github.com", ""):
            raise InvalidPR(command=command)

        path = url.path
        while path and path.startswith("/"):
            path = path[1:]
        while path and path.endswith("/"):
            path = path[:-1]

        if "/pull/" not in path:
            raise InvalidPR(command=command)

        split = path.split("/")
        if len(split) != 4 or split[2] != "pull":
            raise InvalidPR(command=command)

        organisation, repo, _, pr_number = split
        if not pr_number.isdigit():
            raise InvalidPR(command=command)

        message["pr_to_track"] = {
            "organisation": organisation,
            "repo": repo,
            "pr_number": int(pr_number),
        }
        return super().deserialize(message)
