from typing import Protocol


class PR(Protocol):
    @property
    def organisation(self) -> str: ...

    @property
    def repo(self) -> str: ...

    @property
    def pr_number(self) -> int: ...


class PRRequest(Protocol):
    @property
    def pr(self) -> PR: ...

    @property
    def user_id(self) -> str: ...

    @property
    def channel_id(self) -> str: ...


class Storage(Protocol):
    async def store_pr_request(self, pr_request: PRRequest, /) -> None: ...
