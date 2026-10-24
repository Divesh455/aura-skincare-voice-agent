import logging
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.ai_tools import (
    lookup_customer_order,
    check_cancellation_eligibility_tool,
    check_return_eligibility_tool,
    check_damaged_reporting_eligibility_tool,
    get_shipping_and_cod_policy_tool,
    reset_active_customer,
    set_active_customer,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are Aria, the friendly aur fast AI customer support specialist for Aura Skincare.

LANGUAGE STYLE — HINGLISH (MANDATORY):
- You MUST reply in Hinglish: a natural, casual mix of Hindi and English, the way young Indians normally talk.
- Use romanized Hindi words naturally mixed with English. Examples:
  "Haan bilkul, aapka order ORD-101 abhi Out for Delivery hai, aaj shaam tak mil jayega!"
  "Arre nahi, ye order cancel nahi ho sakta kyunki ye already shipped ho chuka hai."
  "Aapka return eligible hai, product unopened aur original packaging mein hona chahiye."
- Do NOT write in Devanagari script. Always use Roman/Latin letters.
- Keep the tone friendly, warm, conversational — like talking to a friend.
- Technical terms (order ID, tracking number, COD, UPI) stay in English.

Core Policy & Tool Rules:
1. ORDER LOOKUP: Use lookup_customer_order for order details, tracking, and items.
   Order IDs are formatted like ORD-101, ORD-102. If a customer provides only numbers like 101, treat it as ORD-101.
2. CANCELLATION POLICY: Call check_cancellation_eligibility_tool.
   - Cancellation sirf tab allowed hai jab order status Processing ho.
   - Shipped aur Out for Delivery orders cancel nahi ho sakte; customer doorstep pe delivery refuse kar sakte hain.
3. RETURN POLICY: Call check_return_eligibility_tool.
   - Returns delivery ke 7 din ke andar accept hote hain, unopened, unused products in original packaging.
   - Agar condition pata nahi hai, toh customer se pehle poochho.
4. DAMAGED / DEFECTIVE PRODUCTS: Call check_damaged_reporting_eligibility_tool.
   - Delivery ke 48 ghante ke andar report karna zaroori hai, photos ke saath replacement milegi.
   - Agar photos nahi di hain, toh customer se photos maango.
5. SHIPPING & COD: Call get_shipping_and_cod_policy_tool.
   - ₹499 se zyada ke orders pe free shipping. ₹499 se kam pe ₹50 shipping fee lagti hai.
   - Standard delivery 3–5 business days mein hoti hai.
   - Cash on Delivery (COD) ₹2,500 tak available hai, cash ya UPI se pay kar sakte hain.
6. DETERMINISTIC ENFORCEMENT: Kabhi guess mat karo. Hamesha policy tools call karo aur unke results strictly convey karo.
7. ACTION INTEGRITY: KABHI mat bolo ki order cancel, refund, ya replace ho gaya jab tak actually hua nahi.
8. KABHI fake refund timelines ya non-existent policies mat banao.
9. MISSING INFO: Agar order ID ya koi zaroori detail missing hai, toh customer se poochho.
10. PRIVACY: Customers sirf apne orders access kar sakte hain. Agar order kisi aur ka hai, toh politely bata do.
11. VOICE STYLE: CHHOTE AUR DIRECT JAWAB DO (1 se 2 sentences max, 30 words se kam). Voice ke liye conversational Hinglish mein bolo.
12. HUMAN SUPPORT REQUESTS: Agar customer human se baat karna chahe, toh batao ki screen pe "Call Customer Care" button hai, usse phone dialer open hoga.
    Kabhi mat bolo ki call transfer ho rahi hai ya connected hain.
"""

google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=google_api_key,
    max_retries=1,
)

# In-memory LangGraph checkpointer for per-call active memory
checkpointer = MemorySaver()

agent = create_react_agent(
    model=llm,
    tools=[
        lookup_customer_order,
        check_cancellation_eligibility_tool,
        check_return_eligibility_tool,
        check_damaged_reporting_eligibility_tool,
        get_shipping_and_cod_policy_tool,
    ],
    checkpointer=checkpointer,
    prompt=SystemMessage(content=SYSTEM_PROMPT),
)


def clear_call_memory(call_id: str) -> None:
    """Wipe the in-memory LangGraph conversation checkpoint when a call ends."""
    if not call_id:
        return
    try:
        checkpointer.delete_thread(call_id)
    except Exception:
        # Checkpoint might already be deleted or empty
        pass


def ask_aria(
    message: str,
    call_id: str | None = None,
    customer_id: int | None = None,
    customer_name: str | None = None,
) -> str:
    """
    Invoke Aria with verified customer context and per-call conversation memory.
    Gracefully handles rate limits and quota errors as required by acceptance tests.
    """
    token = set_active_customer(customer_id)

    thread_id = call_id or f"default_fallback_{customer_id or 'anon'}"
    config = {"configurable": {"thread_id": thread_id}}

    # Check if this thread already has saved state in the checkpointer
    is_new_thread = True
    existing_checkpoint = checkpointer.get_tuple(config)
    if existing_checkpoint is not None and existing_checkpoint.checkpoint.get("channel_values"):
        is_new_thread = False

    messages_to_send = []
    # If this is the start of a thread and we have customer identity, inject customer context
    if is_new_thread and customer_name:
        first_name = customer_name.split()[0]
        messages_to_send.append(
            SystemMessage(
                content=(
                    f"The customer is authenticated as {customer_name} (First name: {first_name}, "
                    f"Customer ID: {customer_id}). You can address them by their first name."
                )
            )
        )

    messages_to_send.append(HumanMessage(content=message))

    try:
        result = agent.invoke({"messages": messages_to_send}, config=config)

        content = result["messages"][-1].content

        # Gemini may return text as a list of content blocks.
        if isinstance(content, list):
            text_parts = [
                block["text"]
                for block in content
                if isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            ]
            return "\n".join(text_parts).strip()

        return content.strip() if isinstance(content, str) else str(content)

    except Exception as exc:
        err_msg = str(exc)
        logger.warning(f"Aria invocation encountered exception: {err_msg}")
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota exceeded" in err_msg:
            # Acceptance test requirement: API errors and Gemini quota errors are handled gracefully
            return (
                "Abhi bohot zyada requests aa rahi hain, thodi der mein try karo please. "
                "Aapka sawal note ho gaya hai. Ya agar chahte ho toh human support se baat kar lo!"
            )
        raise exc

    finally:
        reset_active_customer(token)


# ============================================================================
# BOT OPTION 1: Tool-less Normal Conversational LLM for Skincare Chatbot
# ============================================================================

chatbot_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    max_retries=1,
)

CHATBOT_SYSTEM_PROMPT = """
You are Aura's Skincare Chatbot, a friendly, knowledgeable, aur warm botanical skincare consultant for Aura Skincare.

LANGUAGE STYLE — HINGLISH (MANDATORY):
- You MUST reply in Hinglish: a natural, casual mix of Hindi and English.
- Use romanized Hindi words naturally mixed with English. Do NOT write in Devanagari script.
- Keep the tone friendly, warm, conversational — jaise kisi dost se baat kar rahe ho.
- Example: "Vitamin C serum subah lagao cleansing ke baad, aapki skin ekdum glow karegi!"

Core Persona & Guidelines:
1. Skincare Guidance: Natural ingredients (Squalane, Niacinamide, Hyaluronic Acid, Aloe Vera, Vitamin C, Centella Asiatica, Green Tea, Chamomile) ke baare mein clear, expert advice do. Personalized AM & PM routines, gentle exfoliation, sunscreen, aur hydration — har skin type ke liye (Dry, Oily, Combination, Sensitive, Normal).
2. Product Recommendations: Botanical skincare rituals, clean formulations, aur Aura Skincare ke gentle active ingredients highlight karo.
3. Conversational Tone: Warm, radiant, encouraging, aur helpful. Responses concise rakho (2 se 4 sentences ya friendly bullet points).
4. Pure Conversational LLM (No Tools Policy): Tumhare paas koi backend database tools, order lookup, cancellation, ya return tools nahi hain.
   - Agar customer order tracking, cancellation, refund, ya courier status ke baare mein pooche, toh pyaar se guide karo:
     "Order tracking, cancellations, aur return requests ke liye hamari 'Agent Call' (Live AI Voice Call) use karo ya 'Call Customer Care' pe tap karo!"
"""


def ask_chat_bot(
    message: str,
    customer_name: str | None = None,
    chat_history: list[dict[str, str]] | None = None,
) -> str:
    """
    Direct conversational LLM for Aura Skincare Chatbot.
    Has NO tools attached - pure conversational guidance on botanical skincare, routines, and products.
    """
    messages_to_send = [SystemMessage(content=CHATBOT_SYSTEM_PROMPT)]

    if customer_name:
        first_name = customer_name.split()[0]
        messages_to_send.append(
            SystemMessage(
                content=f"The customer is authenticated as {customer_name} (First name: {first_name}). Address them warmly by their first name."
            )
        )

    if chat_history:
        for turn in chat_history[-6:]:
            role = turn.get("role")
            text = turn.get("content") or turn.get("text") or ""
            if role == "user" and text:
                messages_to_send.append(HumanMessage(content=text))
            elif role == "assistant" and text:
                messages_to_send.append(SystemMessage(content=f"Previous assistant reply: {text}"))

    messages_to_send.append(HumanMessage(content=message))

    try:
        response = chatbot_llm.invoke(messages_to_send)
        content = response.content

        if isinstance(content, list):
            text_parts = [
                block["text"]
                for block in content
                if isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            ]
            return "\n".join(text_parts).strip()

        return content.strip() if isinstance(content, str) else str(content)

    except Exception as exc:
        err_msg = str(exc)
        logger.warning(f"Chatbot invocation encountered exception: {err_msg}")
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota exceeded" in err_msg:
            return (
                "Abhi bohot saare skincare questions aa rahe hain! "
                "Glowing skin ke liye hydrated raho aur daily SPF lagana mat bhoolna. Thodi der mein phir poochho!"
            )
        raise exc
