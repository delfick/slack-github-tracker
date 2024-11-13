import attrs


@attrs.define
class GithubWebhookError(Exception):
    pass


@attrs.define
class GithubWebhookDropped(Exception):
    event: str
