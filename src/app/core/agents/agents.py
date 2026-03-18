<<<<<<< HEAD
"""
Agent implementations and node functions for the QA pipeline.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.core.agents.state import QAState
from app.core.agents.prompts import (
    PLANNING_SYSTEM_PROMPT,
    RETRIEVAL_SYSTEM_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT
)
from app.core.agents.tools import retrieval_tool
from app.core.retrieval.serialization import serialize_chunks
import re
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# NEW: PLANNING AGENT
# ============================================================================

def create_planning_agent():
    """Create the planning agent LLM."""
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0
    )


def parse_planning_response(response_text: str) -> tuple[str, list[str]]:
    """
    Parse the planning agent's response to extract plan and sub-questions.
    
    Args:
        response_text: Raw text response from planning agent
        
    Returns:
        Tuple of (plan_text, list_of_sub_questions)
    """
    # Extract plan (text after "Plan:" until "Sub-questions:")
    plan_match = re.search(r'Plan:\s*(.+?)(?=Sub-questions:|$)', response_text, re.DOTALL | re.IGNORECASE)
    plan = plan_match.group(1).strip() if plan_match else "No specific plan generated."
    
    # Extract sub-questions (lines starting with - or • or numbered)
    sub_questions = []
    sub_q_section = re.search(r'Sub-questions?:\s*(.+)', response_text, re.DOTALL | re.IGNORECASE)
    
    if sub_q_section:
        lines = sub_q_section.group(1).strip().split('\n')
        for line in lines:
            # Match lines starting with -, •, or numbers like 1., 2.
            cleaned = re.sub(r'^[\s\-•\d.]+', '', line).strip()
            if cleaned:
                sub_questions.append(cleaned)
    
    # If no sub-questions found, use the original question as fallback
    if not sub_questions:
        sub_questions = [response_text.strip()]
    
    return plan, sub_questions


def planning_node(state: QAState) -> dict:
    """
    Planning node: Analyzes the question and creates a search strategy.
    
    This is the first step in the enhanced pipeline.
    """
    question = state["question"]
    
    logger.info(f"🧠 Planning node: Analyzing question: {question}")
    
    # Create planning agent
    llm = create_planning_agent()
    
    # Build messages
    messages = [
        SystemMessage(content=PLANNING_SYSTEM_PROMPT),
        HumanMessage(content=f"Question: {question}")
    ]
    
    # Invoke agent
    response = llm.invoke(messages)
    response_text = response.content
    
    # Parse response
    plan, sub_questions = parse_planning_response(response_text)
    
    logger.info(f"📋 Plan created: {plan}")
    logger.info(f"🔍 Sub-questions: {sub_questions}")
    
    return {
        "plan": plan,
        "sub_questions": sub_questions,
        "messages": [AIMessage(content=response_text, name="planner")]
    }


# ============================================================================
# RETRIEVAL AGENT (UPDATED)
# ============================================================================

def create_retrieval_agent():
    """Create the retrieval agent with tool binding."""
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0
    )
    return llm.bind_tools([retrieval_tool])


def retrieval_node(state: QAState) -> dict:
    """
    Retrieval node: Searches for relevant information using the plan.
    
    Enhanced to use planning information.
    """
    question = state["question"]
    plan = state.get("plan", "No specific plan provided.")
    sub_questions = state.get("sub_questions", [])
    
    logger.info(f"🔎 Retrieval node: Executing search with plan")
    
    # Format sub-questions for prompt
    sub_q_text = "\n".join([f"- {q}" for q in sub_questions]) if sub_questions else "- " + question
    
    # Build system prompt with planning context
    system_prompt = RETRIEVAL_SYSTEM_PROMPT.format(
        plan=plan,
        sub_questions=sub_q_text
    )
    
    # Create agent
    agent = create_retrieval_agent()
    
    # Build messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Search for information to answer: {question}")
    ]
    
    # Agent loop: Let agent make multiple tool calls if needed
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        response = agent.invoke(messages)
        messages.append(response)
        
        # Check if agent wants to use tools
        if not response.tool_calls:
            break
        
        # Execute tool calls
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            logger.info(f"🔧 Calling {tool_name} with query: {tool_args.get('query', '')}")
            
            if tool_name == "retrieval_tool":
                # Execute retrieval
                result = retrieval_tool.invoke(tool_args)
                
                # Add tool result to messages
                from langchain_core.messages import ToolMessage
                messages.append(
                    ToolMessage(
                        content=result,
                        tool_call_id=tool_call["id"]
                    )
                )
        
        iteration += 1
    
    # Extract all context from tool messages
    context_parts = []
    for msg in messages:
        if hasattr(msg, 'type') and msg.type == "tool":
            context_parts.append(msg.content)
    
    context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant information found."
    
    logger.info(f"📚 Retrieved context length: {len(context)} characters")
    
    return {
        "context": context,
        "messages": messages
    }


# ============================================================================
# SUMMARIZATION AGENT
# ============================================================================

def create_summarization_agent():
    """Create the summarization agent."""
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0
    )


def summarization_node(state: QAState) -> dict:
    """
    Summarization node: Creates a clear answer from retrieved context.
    """
    question = state["question"]
    context = state.get("context", "")
    
    logger.info(f"✍️ Summarization node: Creating answer")
    
    if not context or context == "No relevant information found.":
        return {
            "answer": "I couldn't find relevant information to answer this question.",
            "messages": [AIMessage(content="No context available", name="summarizer")]
        }
    
    # Create agent
    llm = create_summarization_agent()
    
    # Build messages
    messages = [
        SystemMessage(content=SUMMARIZATION_SYSTEM_PROMPT),
        HumanMessage(content=f"""
Question: {question}

Context:
{context}

Please provide a clear, comprehensive answer based on this context.
""")
    ]
    
    # Invoke agent
    response = llm.invoke(messages)
    answer = response.content
    
    logger.info(f"✅ Answer generated: {len(answer)} characters")
    
    return {
        "answer": answer,
        "messages": [AIMessage(content=answer, name="summarizer")]
    }


# ============================================================================
# VERIFICATION AGENT
# ============================================================================

def create_verification_agent():
    """Create the verification agent."""
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0
    )


def verification_node(state: QAState) -> dict:
    """
    Verification node: Checks answer quality and accuracy.
    """
    question = state["question"]
    context = state.get("context", "")
    answer = state.get("answer", "")
    
    logger.info(f"✔️ Verification node: Checking answer quality")
    
    # Create agent
    llm = create_verification_agent()
    
    # Build messages
    messages = [
        SystemMessage(content=VERIFICATION_SYSTEM_PROMPT),
        HumanMessage(content=f"""
Question: {question}

Context:
{context}

Answer:
{answer}

Please verify this answer and provide corrections if needed, or confirm it's accurate.
""")
    ]
    
    # Invoke agent
    response = llm.invoke(messages)
    verified_answer = response.content
    
    logger.info(f"✅ Verification complete")
    
    return {
        "answer": verified_answer,
        "messages": [AIMessage(content=verified_answer, name="verifier")]
    }
=======


from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from .state import QAState
from .prompts import (
    QUERY_PLANNER_PROMPT,
    SUMMARIZATION_PROMPT,
    VERIFICATION_PROMPT
)
from .tools import retrieval_tool


# Initialize Gemini LLMs 
planner_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    convert_system_message_to_human=True
)

summarization_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    convert_system_message_to_human=True
)

verification_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    convert_system_message_to_human=True
)


def planning_node(state: QAState) -> dict:
    """Planning Agent: Analyzes question and creates search plan."""
    question = state["question"]
    
    print(f"\n PLANNING AGENT: Analyzing question...")
    
    prompt = f"{QUERY_PLANNER_PROMPT}\n\nUser Question: {question}"
    response = planner_llm.invoke([HumanMessage(content=prompt)])
    
    text = response.content
    print(f"Planning output:\n{text}\n")
    
    # Parse response
    plan = ""
    sub_questions = []
    
    if "PLAN:" in text:
        parts = text.split("PLAN:")[1].split("SUB_QUESTIONS:")
        plan = parts[0].strip()
    
    if "SUB_QUESTIONS:" in text:
        lines = text.split("SUB_QUESTIONS:")[1].strip().split("\n")
        sub_questions = [
            line.replace("-", "").replace("•", "").strip() 
            for line in lines 
            if line.strip() and not line.strip().startswith("Example")
        ]
    
    return {
        "plan": plan,
        "sub_questions": sub_questions
    }


def retrieval_node(state: QAState) -> dict:
    """Retrieval Agent: Multi-query search in Pinecone."""
    question = state["question"]
    plan = state.get("plan", "")
    sub_questions = state.get("sub_questions", [])
    
    print(f"\n RETRIEVAL AGENT: Searching Pinecone...")
    
    # Strategy 1: Search with original question
    print(f"   → Search 1: Original question")
    context_parts = [retrieval_tool.invoke({"query": question})]
    
    # Strategy 2: Search with sub-questions
    if sub_questions:
        print(f"   → Searches 2-{len(sub_questions)+1}: Sub-questions")
        for i, sub_q in enumerate(sub_questions[:3], 2):
            print(f"      • Search {i}: {sub_q[:50]}...")
            result = retrieval_tool.invoke({"query": sub_q})
            context_parts.append(result)
    
    # Combine all context
    combined_context = "\n\n" + ("="*60 + "\n\n").join(context_parts)
    
    print(f" Completed {len(context_parts)} Pinecone searches")
    
    return {"context": combined_context}


def summarization_node(state: QAState) -> dict:
    """Summarization Agent: Generate answer."""
    question = state["question"]
    context = state.get("context", "")
    
    print(f"\n SUMMARIZATION AGENT: Generating answer...")
    
    prompt = f"{SUMMARIZATION_PROMPT}\n\nQuestion: {question}\n\nContext:\n{context}"
    response = summarization_llm.invoke([HumanMessage(content=prompt)])
    
    answer = response.content
    print(f"Generated answer: {answer[:100]}...\n")
    
    return {"answer": answer}


# def verification_node(state: QAState) -> dict:
#     """Verification Agent: Validate answer quality."""
#     question = state["question"]
#     answer = state.get("answer", "")
#     context = state.get("context", "")
    
#     print(f"\n✅ VERIFICATION AGENT: Checking quality...")
    
#     prompt = f"{VERIFICATION_PROMPT}\n\nQuestion: {question}\n\nAnswer: {answer}\n\nContext: {context}"
#     response = verification_llm.invoke([HumanMessage(content=prompt)])
    
#     verified_answer = response.content
#     print(f"Verification complete.\n")
    
#     return {"answer": verified_answer}

def verification_node(state: QAState) -> dict:
    """
    Verification Agent: Validates and refines the answer.
    Returns the final polished answer.
    """
    question = state["question"]
    answer = state.get("answer", "")
    context = state.get("context", "")
    
    print(f"\n✅ VERIFICATION AGENT: Reviewing answer quality...")
    
    # Improved prompt that focuses on output quality
    verification_prompt = f"""You are a Quality Verification Agent. Review the answer below and return the FINAL ANSWER.

Question:
{question}

Current Answer:
{answer}

Available Context:
{context[:500]}...

Your task:
1. If the answer is accurate and complete → Return it EXACTLY as written
2. If the answer needs improvement → Return an IMPROVED version
3. Remove any meta-commentary like "based on the context"
4. Ensure the answer directly addresses the question

IMPORTANT: Return ONLY the final answer text. Do NOT include:
- Your analysis or reasoning
- Phrases like "The answer is accurate" or "Return as-is"
- Meta-commentary about the answer quality

Final Answer:"""
    
    response = verification_llm.invoke([HumanMessage(content=verification_prompt)])
    verified_answer = response.content.strip()
    
    # Safety check: detect if LLM returned analysis instead of answer
    meta_phrases = [
        "the answer is",
        "return the answer",
        "as-is",
        "accurate and complete",
        "well-structured",
        "directly supported"
    ]
    
    # If response contains meta-commentary, use original answer
    if any(phrase in verified_answer.lower() for phrase in meta_phrases):
        print("⚠️  Verification returned analysis - using original answer")
        verified_answer = answer
    else:
        print(f"✅ Verification complete - {len(verified_answer)} characters")
    
    print()
    
    return {"answer": verified_answer}


>>>>>>> d64bd48 (Initial commit)
