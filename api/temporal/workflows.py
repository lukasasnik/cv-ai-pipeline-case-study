"""
Temporal workflow definitions for CV processing.
"""

from datetime import timedelta

from temporalio import workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from temporal.activities import extract_cv_text, set_execution_state
    from models import ExecutionState


@workflow.defn
class CvProcessingWorkflow:
    """Orchestrates the CV processing pipeline."""

    @workflow.run
    async def run(self, cv_execution_id: int) -> str:
        """
        Execute the CV processing pipeline.

        Args:
            cv_execution_id: ID of the CvExecution to process.

        Returns:
            Processing result summary.
        """
        # Set state to PROGRESS
        await workflow.execute_activity(
            set_execution_state,
            args=[cv_execution_id, ExecutionState.PROGRESS.value],
            start_to_close_timeout=timedelta(seconds=10),
        )

        try:
            # Extract text
            artifact_id = await workflow.execute_activity(
                extract_cv_text,
                args=[cv_execution_id],
                start_to_close_timeout=timedelta(minutes=5),
            )
            
            # If successful, set state to SUCCESS
            await workflow.execute_activity(
                set_execution_state,
                args=[cv_execution_id, ExecutionState.SUCCESS.value],
                start_to_close_timeout=timedelta(seconds=10),
            )
            return f"Success: Extracted artifact {artifact_id}"

        except ApplicationError as e:
            # Set state to ERROR and re-raise to fail the workflow
            await workflow.execute_activity(
                set_execution_state,
                args=[cv_execution_id, ExecutionState.ERROR.value],
                start_to_close_timeout=timedelta(seconds=10),
            )
            raise e
