<<<<<<< HEAD
from typing import TypedDict, Annotated
from langgraph.graph import add_messages


class QAState(TypedDict):
    """
    State schema for the QA pipeline with query planning support.
    """
    # Core fields
    question: str
    context: str | None
    answer: str | None
    
    # Message history for agent communication
    messages: Annotated[list, add_messages]
    
    # NEW: Query planning fields
    plan: str | None
    sub_questions: list[str] | None
    
    # Optional: Track which sources were used
    sources: list[str] | None
=======
from typing import TypedDict


class QAState(TypedDict):
    """State for the QA pipeline."""
    
    # Input
    question: str
    
    # Planning (NEW for Feature 1)
    plan: str | None
    sub_questions: list[str] | None
    
    # Retrieval
    context: str | None
    
    # Answer Generation
    answer: str | None
>>>>>>> d64bd48 (Initial commit)
