from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.graph.prompts import WRITER_PROMPT
from src.graph.llms import get_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)

class WriterInput(BaseModel):
    research_findings: str = Field(description="The complete research findings, context, and strict instructions for the writer to format into the final response.")
    user_query: str = Field(description="The original query or task from the user.")

@tool("writer_tool", args_schema=WriterInput)
def writer_tool(research_findings: str, user_query: str) -> str:
    """
    Constructs the final, structured, and polished response for the user.
    Use this tool ONLY when you have gathered all necessary information and are ready to finalize your answer.
    """
    logger.info("── writer_tool ── drafting final response")
    llm = get_llm("efficiency-edge")
    prompt = ChatPromptTemplate.from_messages([
        ("system", WRITER_PROMPT),
        ("human", "User Query: {user_query}\n\nResearch Findings & Instructions:\n{research_findings}")
    ])
    
    chain = prompt | llm
    try:
        response = chain.invoke({
            "user_query": user_query,
            "research_findings": research_findings
        })
        return f"FINAL DRAFT (Output this exactly to the user):\n\n{response.content}"
    except Exception as e:
        logger.error("Writer tool failed: %s", e)
        return f"Writer tool encountered an error: {e}. Please format the findings yourself."
