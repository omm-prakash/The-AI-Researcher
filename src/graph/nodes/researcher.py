from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from src.graph.state import AgentState
from src.graph.prompts import RESEARCHER_PROMPT
from src.graph.llms import get_llm
from src.tools.search import tavily_search_tool, tavily_extract_tool
from src.tools.file_extractors import pdf_extractor_tool, image_extractor_tool, audio_extractor_tool
from src.tools.writer_tool import writer_tool
from src.utils.context import trim_history, flatten_for_text_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)


def researcher_node(state: AgentState):
    """
    Researcher: Performs web research and uses file extraction tools to answer the user's query.
    """
    logger.info("── Researcher ── starting research")

    messages = state.get("messages", [])
    logger.debug("Researcher: %d messages in context", len(messages))

    llm = get_llm("agentic-systems")

    attachment_type = state.get("attachment_type", "none")
    attachment_path = state.get("attachment_path", "")

    tools = [tavily_search_tool, tavily_extract_tool, writer_tool]
    dynamic_tool_list = ""
    attachment_instructions = ""

    if attachment_type != "none" and attachment_path:
        logger.info("Researcher: attachment configured: %s [%s]", attachment_path, attachment_type)
        if attachment_type == "pdf":
            tools.append(pdf_extractor_tool)
            dynamic_tool_list = "4. **pdf_extractor_tool** — Use this to extract information from the attached PDF document."
            attachment_instructions = (
                f"\n[ATTACHMENT CONTEXT]\n"
                f"The user has attached a PDF file located at: `{attachment_path}`.\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. You MUST NOT try to look for the file directly, search for it online, or pretend you can read it.\n"
                "2. Instead, you MUST use the `pdf_extractor_tool` with the exact path provided above to retrieve the file's information.\n"
                "3. Use the information shared by the file extractor tool to answer the user's query."
            )
        elif attachment_type == "image":
            tools.append(image_extractor_tool)
            dynamic_tool_list = "4. **image_extractor_tool** — Use this to extract and analyze visual data from the attached image."
            attachment_instructions = (
                f"\n[ATTACHMENT CONTEXT]\n"
                f"The user has attached an image file located at: `{attachment_path}`.\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. You MUST NOT try to look for the image directly, search for it online, or pretend you can see it.\n"
                "2. Instead, you MUST use the `image_extractor_tool` with the exact path provided above to retrieve the image analysis.\n"
                "3. Use the information shared by the file extractor tool to answer the user's query."
            )
        elif attachment_type == "audio":
            tools.append(audio_extractor_tool)
            dynamic_tool_list = "4. **audio_extractor_tool** — Use this to transcribe and analyze the attached audio file."
            attachment_instructions = (
                f"\n[ATTACHMENT CONTEXT]\n"
                f"The user has attached an audio file located at: `{attachment_path}`.\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. You MUST NOT try to look for the audio directly, search for it online, or pretend you can hear it.\n"
                "2. Instead, you MUST use the `audio_extractor_tool` with the exact path provided above to retrieve the audio transcription and analysis.\n"
                "3. Use the information shared by the file extractor tool to answer the user's query."
            )

    llm_with_tools = llm.bind_tools(tools)

    system_content = RESEARCHER_PROMPT.format(
        dynamic_tool_list=dynamic_tool_list,
        attachment_context=attachment_instructions
    )
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_content),
        ("placeholder", "{messages}"),
    ])

    try:
        chain = prompt | llm_with_tools
        response = chain.invoke({"messages": messages})
        logger.info("Researcher: research complete → routing to Writer")
    except Exception as e:
        logger.error("Researcher: LLM call failed: %s", e, exc_info=True)
        raise
    
    return {"messages": [response]}
