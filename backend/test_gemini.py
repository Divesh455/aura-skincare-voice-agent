
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.ai_tools import lookup_customer_order

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY is missing from backend/.env")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
)

tools = [lookup_customer_order]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)

messages = [
    SystemMessage(
        content=(
            "You are Aria, a friendly customer support agent for Aura Skincare. "
            "Use the order lookup tool for order-specific questions. "
            "Base your answers on the actual tool results. Never invent "
            "order details. Keep your answers concise and natural for speech."
        )
    ),
    HumanMessage(
        content="Can you check order ORD-101 and tell me its current status?"
    ),
]

# Step 1: Ask Gemini what to do.
response = llm_with_tools.invoke(messages)
messages.append(response)

# Step 2: Execute any tool calls requested by Gemini.
for tool_call in response.tool_calls:
    selected_tool = tools_by_name.get(tool_call["name"])

    if selected_tool is None:
        raise RuntimeError(f"Unknown tool: {tool_call['name']}")

    result = selected_tool.invoke(tool_call["args"])

    messages.append(
        ToolMessage(
            content=result,
            tool_call_id=tool_call["id"],
        )
    )

# Step 3: Ask Gemini to answer using the tool result.
final_response = llm.invoke(messages)

print("\nAria's response:")
print(final_response.content)
