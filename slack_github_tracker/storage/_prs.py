from sqlalchemy import Column, Integer, Table, Text

from ._metadata import metadata

pr_requests_table = Table(
    "pr_requests",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("organisation", Text),
    Column("repo", Text),
    Column("pr_number", Integer),
)
