"""
Temporal workflow definitions for CV processing.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from temporal.activities import process_cv


@workflow.defn
class CvProcessingWorkflow:
    """Orchestrates the CV processing pipeline."""

    @workflow.run
    async def run(self, cv_record_id: str) -> str:
        """
        Execute the CV processing pipeline.

        Args:
            cv_record_id: UUID of the CvRecord to process.

        Returns:
            Processing result summary.
        """
        result = await workflow.execute_activity(
            process_cv,
            cv_record_id,
            start_to_close_timeout=timedelta(minutes=5),
        )
        return result
