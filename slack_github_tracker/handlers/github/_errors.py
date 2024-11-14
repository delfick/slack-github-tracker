import attrs


@attrs.define
class GithubWebhookError(Exception):
    pass


@attrs.define(kw_only=True)
class GithubWebhookDropped(Exception):
    reason: str
