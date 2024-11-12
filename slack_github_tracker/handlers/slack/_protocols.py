from __future__ import annotations

from typing import Protocol

import slack_bolt


class Deserializer[T_Message](Protocol):
    def deserialize(self, message: dict[str, object]) -> T_Message: ...


class Responder[T_Message](Protocol):
    async def __call__(self, message: T_Message, say: slack_bolt.async_app.AsyncSay) -> None: ...
