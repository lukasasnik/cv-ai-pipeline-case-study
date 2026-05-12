"""
Temporal worker entrypoint.

Run this module directly to start the worker:
    python -m temporal.worker
"""

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from config import settings
from temporal.activities import extract_cv_text, set_execution_state
from temporal.workflows import CvProcessingWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Connect to Temporal and run the worker."""
    logger.info(
        "Connecting to Temporal at %s ...", settings.temporal_host
    )

    client = await Client.connect(settings.temporal_host)

    logger.info(
        "Starting worker on task queue: %s", settings.temporal_task_queue
    )

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[CvProcessingWorkflow],
        activities=[extract_cv_text, set_execution_state],
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
