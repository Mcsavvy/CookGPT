"""Prompts for the chatbot."""
from pathlib import Path

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)

from cookgpt.ext.config import config

system_prompt_template = SystemMessagePromptTemplate.from_template_file(
    Path(__file__).parent / "templates" / "system_prompt.txt",
    input_variables=["user"],
)

prompt = ChatPromptTemplate.from_messages(
    [
        system_prompt_template,
        MessagesPlaceholder(variable_name=config.CHATBOT_MEMORY_KEY),
        MessagesPlaceholder(variable_name=config.CHATBOT_CHAIN_INPUT_KEY),
    ]
)


# Current conversation:
# {%s}
# {user}: {%s}
# Cookgpt:""" % (
#     config.CHATBOT_MEMORY_KEY,
#     config.CHATBOT_CHAIN_INPUT_KEY,
# )

# PROMPT = ChatPromptTemplate.from_messages([("system", SYSTEM_MESSAGE)])
