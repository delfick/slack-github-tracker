from typing import Protocol


class Deserializer[T_Message](Protocol):
    def deserialize(self, message: dict[str, object]) -> T_Message: ...
