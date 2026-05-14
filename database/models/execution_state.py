import enum

class ExecutionState(enum.Enum):
    SUCCESS = "success"
    ERROR = "error"
    PROGRESS = "progress"
    NEW = "new"
