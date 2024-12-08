from sqlalchemy.orm import Mapped, mapped_column

from ._metadata import Base


class Request(Base):
    __tablename__ = "pr_requests"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    organisation: Mapped[str]
    repo: Mapped[str]
    pr_number: Mapped[int]
    user_id: Mapped[str]
    channel_id: Mapped[str]
