"""
NotifyAI V4.2 Professional
Scheduler Engine
"""

from __future__ import annotations

import logging
import signal
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ==========================================================
# Scheduled Task
# ==========================================================

@dataclass(slots=True)
class ScheduledTask:
    """
    Represents one scheduled task.
    """

    name: str

    interval: int

    callback: Callable

    enabled: bool = True

    last_run: Optional[datetime] = None

    next_run: Optional[datetime] = None


# ==========================================================
# Scheduler
# ==========================================================

class Scheduler:

    """
    Professional Background Scheduler.
    """

    def __init__(self):

        self.tasks: List[ScheduledTask] = []

        self.running = False

        self.thread: Optional[threading.Thread] = None

        self.lock = threading.Lock()

    # ------------------------------------------------------

    def register(

        self,

        name: str,

        interval: int,

        callback: Callable,

    ):

        """
        Register task.
        """

        task = ScheduledTask(

            name=name,

            interval=interval,

            callback=callback,

        )

        self.tasks.append(task)

        logger.info(

            "Registered task: %s",

            name,

        )

    # ------------------------------------------------------

    def unregister(

        self,

        name: str,

    ):

        """
        Remove task.
        """

        self.tasks = [

            t

            for t in self.tasks

            if t.name != name

        ]

        logger.info(

            "Removed task: %s",

            name,

        )

    # ------------------------------------------------------

    def start(self):

        """
        Start scheduler.
        """

        if self.running:

            return

        self.running = True

        self.thread = threading.Thread(

            target=self.run,

            daemon=True,

        )

        self.thread.start()

        logger.info(

            "Scheduler started."

        )

    # ------------------------------------------------------

    def stop(self):

        """
        Stop scheduler.
        """

        self.running = False

        logger.info(

            "Scheduler stopped."

        )
            # ------------------------------------------------------
    # Main Scheduler Loop
    # ------------------------------------------------------

    def run(self):
        """
        Background scheduler loop.
        """

        logger.info("Scheduler loop started.")

        while self.running:

            now = datetime.now()

            with self.lock:

                for task in self.tasks:

                    if not task.enabled:
                        continue

                    if task.last_run is None:

                        self.execute(task)

                        continue

                    elapsed = (
                        now - task.last_run
                    ).total_seconds()

                    if elapsed >= task.interval:

                        self.execute(task)

            time.sleep(1)

        logger.info("Scheduler loop stopped.")

    # ------------------------------------------------------
    # Execute Task
    # ------------------------------------------------------

    def execute(
        self,
        task: ScheduledTask,
    ):
        """
        Execute scheduled task.
        """

        logger.info(
            "Executing task: %s",
            task.name,
        )

        try:

            start = time.perf_counter()

            task.callback()

            runtime = round(
                time.perf_counter() - start,
                3,
            )

            task.last_run = datetime.now()

            logger.info(
                "Task '%s' completed in %.3f sec.",
                task.name,
                runtime,
            )

        except Exception as exc:

            logger.exception(
                "Task '%s' failed: %s",
                task.name,
                exc,
            )

    # ------------------------------------------------------
    # Enable Task
    # ------------------------------------------------------

    def enable(
        self,
        name: str,
    ):

        for task in self.tasks:

            if task.name == name:

                task.enabled = True

                logger.info(
                    "Enabled task: %s",
                    name,
                )

                return

    # ------------------------------------------------------
    # Disable Task
    # ------------------------------------------------------

    def disable(
        self,
        name: str,
    ):

        for task in self.tasks:

            if task.name == name:

                task.enabled = False

                logger.info(
                    "Disabled task: %s",
                    name,
                )

                return

    # ------------------------------------------------------
    # Get Task
    # ------------------------------------------------------

    def get_task(
        self,
        name: str,
    ) -> Optional[ScheduledTask]:

        for task in self.tasks:

            if task.name == name:

                return task

        return None

    # ------------------------------------------------------
    # List Tasks
    # ------------------------------------------------------

    def list_tasks(
        self,
    ) -> List[ScheduledTask]:

        return list(self.tasks)
        # ------------------------------------------------------
    # Execute Once
    # ------------------------------------------------------

    def execute_once(
        self,
        callback: Callable,
    ):
        """
        Execute a callback immediately.
        """

        try:

            logger.info("Executing one-time task.")

            callback()

        except Exception as exc:

            logger.exception(
                "One-time task failed: %s",
                exc,
            )

    # ------------------------------------------------------
    # Schedule Delayed Task
    # ------------------------------------------------------

    def schedule_after(
        self,
        seconds: int,
        callback: Callable,
    ):
        """
        Execute callback after a delay.
        """

        def delayed():

            logger.info(
                "Delayed task scheduled (%s sec).",
                seconds,
            )

            time.sleep(seconds)

            if self.running:

                try:

                    callback()

                except Exception as exc:

                    logger.exception(
                        "Delayed task failed: %s",
                        exc,
                    )

        thread = threading.Thread(
            target=delayed,
            daemon=True,
        )

        thread.start()

        return thread

    # ------------------------------------------------------
    # Retry Task
    # ------------------------------------------------------

    def retry_task(
        self,
        callback: Callable,
        retries: int = 3,
        delay: int = 5,
    ) -> bool:
        """
        Retry callback on failure.
        """

        for attempt in range(1, retries + 1):

            try:

                callback()

                logger.info(
                    "Retry task succeeded (attempt %s).",
                    attempt,
                )

                return True

            except Exception as exc:

                logger.warning(
                    "Retry %s/%s failed: %s",
                    attempt,
                    retries,
                    exc,
                )

                if attempt < retries:

                    time.sleep(delay)

        logger.error("Retry task failed permanently.")

        return False

    # ------------------------------------------------------
    # Health Check
    # ------------------------------------------------------

    def health(self) -> Dict:

        return {

            "running": self.running,

            "tasks": len(self.tasks),

            "thread_alive": (
                self.thread.is_alive()
                if self.thread
                else False
            ),

            "timestamp": datetime.now().isoformat(),

        }

    # ------------------------------------------------------
    # Wait Until Finished
    # ------------------------------------------------------

    def join(
        self,
        timeout: Optional[int] = None,
    ):

        if self.thread:

            self.thread.join(timeout)

    # ------------------------------------------------------
    # Graceful Shutdown
    # ------------------------------------------------------

    def shutdown(self):

        logger.info(
            "Graceful shutdown requested."
        )

        self.stop()

        self.join(5)

    # ------------------------------------------------------
    # Signal Registration
    # ------------------------------------------------------

    def register_signals(self):

        def handler(signum, frame):

            logger.info(
                "Received signal %s",
                signum,
            )

            self.shutdown()

        signal.signal(
            signal.SIGINT,
            handler,
        )

        signal.signal(
            signal.SIGTERM,
            handler,
        )
            # ------------------------------------------------------
    # Scheduler Statistics
    # ------------------------------------------------------

    def statistics(self) -> Dict:
        """
        Return scheduler statistics.
        """

        enabled = sum(
            1 for task in self.tasks if task.enabled
        )

        disabled = len(self.tasks) - enabled

        return {
            "running": self.running,
            "total_tasks": len(self.tasks),
            "enabled_tasks": enabled,
            "disabled_tasks": disabled,
            "thread_alive": (
                self.thread.is_alive()
                if self.thread
                else False
            ),
        }

    # ------------------------------------------------------
    # Update Task Interval
    # ------------------------------------------------------

    def update_interval(
        self,
        name: str,
        interval: int,
    ) -> bool:
        """
        Update task interval.
        """

        task = self.get_task(name)

        if task is None:
            return False

        task.interval = interval

        logger.info(
            "Updated '%s' interval to %s seconds.",
            name,
            interval,
        )

        return True

    # ------------------------------------------------------
    # Reset Task
    # ------------------------------------------------------

    def reset_task(
        self,
        name: str,
    ) -> bool:
        """
        Reset last execution time.
        """

        task = self.get_task(name)

        if task is None:
            return False

        task.last_run = None
        task.next_run = None

        logger.info(
            "Reset task: %s",
            name,
        )

        return True

    # ------------------------------------------------------
    # Clear Tasks
    # ------------------------------------------------------

    def clear(self):
        """
        Remove every scheduled task.
        """

        self.tasks.clear()

        logger.info("All scheduled tasks removed.")

    # ------------------------------------------------------
    # Context Manager
    # ------------------------------------------------------

    def __enter__(self):

        self.start()

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):

        self.shutdown()

    # ------------------------------------------------------
    # String Representation
    # ------------------------------------------------------

    def __repr__(self):

        return (
            f"<Scheduler "
            f"tasks={len(self.tasks)} "
            f"running={self.running}>"
        )


# ==========================================================
# Module Exports
# ==========================================================

__all__ = [
    "Scheduler",
    "ScheduledTask",
]

logger.info(
    "Scheduler Engine Loaded Successfully."
)
