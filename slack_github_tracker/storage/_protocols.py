from typing import Protocol


class PR(Protocol):
    @property
    def organisation(self) -> str: ...

    @property
    def repo(self) -> str: ...

    @property
    def pr_number(self) -> int: ...


class Storage(Protocol):
    async def store_pr_request(self, pr: PR) -> None: ...
