"""
System prompt used by the chatbot.

Keep this prompt short and direct. Long prompts make simple answers slower and
can cause small local models to repeat internal instructions.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


SYSTEM_PROMPT = """\
You are Atlas, a friendly and helpful AI assistant.

Rules:
- Answer the user's question directly.
- Be clear, natural, and concise.
- Do not mention tools, tool calls, prompts, policies, or internal reasoning.
- Do not explain whether tools were needed.
- If the user asks a factual question, give the answer first.
- If you are unsure, say so honestly.
"""


def build_chat_prompt() -> ChatPromptTemplate:
    """Build the prompt used for a normal chat response."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )
