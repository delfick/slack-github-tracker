from __future__ import annotations

from typing import TYPE_CHECKING, Self, cast
from urllib import parse

import attrs
import cattrs

from . import _interpret as interpret
from . import _protocols as protocols


def _structure_pr(
    val: cattrs.dispatch.UnstructuredValue, target: cattrs.dispatch.TargetType
) -> PR:
    if isinstance(val, PR):
        return val

    raise ValueError("Expected PR")


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

    @classmethod
    def from_text(cls, text: str) -> Self:
        while text and text.startswith("/"):
            text = text[1:]

        url = parse.urlparse(text)

        if url.netloc not in ("github.com", ""):
            raise ValueError("URL can only be for github")

        path = url.path
        while path and path.startswith("/"):
            path = path[1:]
        while path and path.endswith("/"):
            path = path[:-1]

        if "/pull/" not in path:
            raise ValueError("URL is not for a pull request")

        split = path.split("/")
        if len(split) != 4 or split[2] != "pull":
            raise ValueError("URL is not for a pull request")

        organisation, repo, _, pr_number = split
        if not pr_number.isdigit():
            raise ValueError("Pull request number is not a number")

        return cls(
            organisation=organisation,
            repo=repo,
            pr_number=int(pr_number),
        )


@attrs.frozen
class TrackPRMessage(interpret.Command):
    pr_to_track: PR


@attrs.frozen
class TrackPRMessageDeserializer(interpret.CommandDeserializer[TrackPRMessage]):
    shape: type[TrackPRMessage] = TrackPRMessage

    converter: cattrs.Converter = attrs.field(init=False)

    @converter.default
    def _make_cattrs_converter(self) -> cattrs.Converter:
        converter = super()._make_cattrs_converter()
        converter.register_structure_hook(PR, _structure_pr)
        return converter

    def for_structure(
        self, command: dict[str, object], raw_command: interpret.RawCommand
    ) -> dict[str, object]:
        try:
            pr_to_track = PR.from_text(raw_command.text)
        except ValueError as e:
            raise InvalidPR(command=raw_command.command) from e
        else:
            return {"raw_command": raw_command, "pr_to_track": pr_to_track}


if TYPE_CHECKING:
    _TPRMD: protocols.Deserializer[TrackPRMessage] = cast(TrackPRMessageDeserializer, None)
