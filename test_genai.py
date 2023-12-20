from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_google_genai import ChatGoogleGenerativeAI

from cookgpt.ext.config import config  # noqa: F401


class Memory(ConversationBufferMemory):
    input_key: str = "input"

    @property
    def memory_variables(self) -> list[str]:
        """Will always return list of memory variables.

        :meta private:
        """
        return [self.memory_key, "name"]


prompt = ChatPromptTemplate.from_messages(
    [
        HumanMessagePromptTemplate.from_template("You are an AI named {name}"),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{input}"),
    ]
)
memory = Memory(input_key="input", output_key="response")
llm = ChatGoogleGenerativeAI(model="gemini-pro")  # type: ignore[call-arg]
chain = ConversationChain(llm=llm, prompt=prompt, memory=memory)
result = chain.predict(
    input="Hello, my name is Bob",
    name="Bard",
    history=[HumanMessage(content="Hello, my name is Bob")],
)
# contents = content_types.to_contents(content)
# print(f"content: {contents}")
# model: GenerativeModel = llm._generative_model
# model.generate_content
# print(f"prompt: {model.co}")
# client: GenerativeServiceClient = model._client
# count = client.count_tokens(contents=contents, model=model.model_name)
# print(f"count: {count.total_tokens}")
