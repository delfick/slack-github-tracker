import asyncio

from machinery import helpers as hp

from slack_github_tracker import protocols
from slack_github_tracker.handlers import background


async def some_task(
    final_fut: asyncio.Future[None], log: list[str | tuple[str, Exception]], prefix: str
) -> None:
    log.append(prefix)
    try:
        await final_fut
    except asyncio.CancelledError:
        log.append(f"{prefix}.cancelled")
    except Exception as exc:
        log.append((prefix, exc))
    finally:
        log.append(f"{prefix}.done")


class TestBackgroundTasks:
    async def test_it_can_register_tasks_before_and_after_running(
        self, logger: protocols.Logger
    ) -> None:
        futs: list[asyncio.Future[None]] = []
        log: list[str | tuple[str, Exception]] = []

        def add_tasks(final_fut: asyncio.Future[None], task_holder: hp.TaskHolder) -> None:
            futs.append(final_fut)
            task_holder.add(some_task(final_fut, log, "t1"))
            task_holder.add(some_task(final_fut, log, "t2"))

        def add_tasks2(final_fut: asyncio.Future[None], task_holder: hp.TaskHolder) -> None:
            futs.append(final_fut)
            task_holder.add(some_task(final_fut, log, "t3"))
            task_holder.add(some_task(final_fut, log, "t4"))

        tasks = background.tasks.Tasks(logger=logger)
        tasks.append(add_tasks)

        assert log == []

        async with tasks.runner() as info:
            await asyncio.sleep(0.1)
            assert futs == [info.final_fut]
            assert log == ["t1", "t2"]

            tasks.append(add_tasks2)
            await asyncio.sleep(0.1)
            assert futs == [info.final_fut, info.final_fut]
            assert log == ["t1", "t2", "t3", "t4"]

            await asyncio.sleep(0.1)

        assert futs == [info.final_fut, info.final_fut]
        assert log == [
            "t1",
            "t2",
            "t3",
            "t4",
            "t1.cancelled",
            "t1.done",
            "t2.cancelled",
            "t2.done",
            "t3.cancelled",
            "t3.done",
            "t4.cancelled",
            "t4.done",
        ]
