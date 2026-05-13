"""
Temporal worker entrypoint.

Run this module directly to start the worker:
    python -m temporal.worker
"""

import asyncio
import logging

from shared.logging_utils import setup_logging

# Initialize logging as early as possible
logger = setup_logging("temporal-worker")

from temporalio.client import Client
from temporalio.worker import Worker

from config import settings
from temporal.activities import extract_cv_text, extract_structured_information, set_execution_state
from temporal.workflows import CvProcessingWorkflow


async def main() -> None:
    """Connect to Temporal and run the worker."""
    logger.info(
        "connecting_to_temporal", host=settings.temporal_host
    )

    client = await Client.connect(settings.temporal_host)

    logger.info(
        "worker_started", task_queue=settings.temporal_task_queue
    )

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[CvProcessingWorkflow],
        activities=[extract_cv_text, extract_structured_information, set_execution_state],
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
