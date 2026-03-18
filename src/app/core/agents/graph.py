<<<<<<< HEAD
"""
LangGraph workflow definition for the QA pipeline.
"""
from langgraph.graph import StateGraph, END
from app.core.agents.state import QAState
from app.core.agents.agents import (
=======


from langgraph.graph import StateGraph, START, END
from .state import QAState
from .agents import (
>>>>>>> d64bd48 (Initial commit)
    planning_node,
    retrieval_node,
    summarization_node,
    verification_node
)
<<<<<<< HEAD
import logging

logger = logging.getLogger(__name__)


def create_qa_graph():
    """
    Create the QA workflow graph with query planning.
    
    Flow: START → planning → retrieval → summarization → verification → END
    """
=======


def create_qa_graph():
    """Create the QA workflow graph."""
    
>>>>>>> d64bd48 (Initial commit)
    # Initialize graph
    graph = StateGraph(QAState)
    
    # Add nodes
    graph.add_node("planning", planning_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("summarization", summarization_node)
    graph.add_node("verification", verification_node)
    
<<<<<<< HEAD
    # Define edges (flow)
    graph.set_entry_point("planning")  # Start with planning
=======
    # Define flow: START → planning → retrieval → summarization → verification → END
    graph.add_edge(START, "planning")
>>>>>>> d64bd48 (Initial commit)
    graph.add_edge("planning", "retrieval")
    graph.add_edge("retrieval", "summarization")
    graph.add_edge("summarization", "verification")
    graph.add_edge("verification", END)
    
<<<<<<< HEAD
    # Compile graph
=======
>>>>>>> d64bd48 (Initial commit)
    return graph.compile()


# Create the compiled graph
<<<<<<< HEAD
qa_graph = create_qa_graph()


def run_qa_flow(question: str) -> QAState:
    """
    Execute the complete QA flow for a given question.
    
    Args:
        question: User's question
        
    Returns:
        Final state containing answer, plan, sub-questions, etc.
    """
    logger.info(f"🚀 Starting QA flow for question: {question}")
    
    # Initialize state
    initial_state = {
        "question": question,
        "context": None,
        "answer": None,
        "plan": None,
        "sub_questions": None,
        "messages": [],
        "sources": None
    }
    
    # Run graph
    final_state = qa_graph.invoke(initial_state)
    
    logger.info(f"🏁 QA flow complete")
    
    return final_state
=======
qa_graph = create_qa_graph()
>>>>>>> d64bd48 (Initial commit)
