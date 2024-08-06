import openai
from openai import OpenAI
import os

client = OpenAI(api_key="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")

assistant = client.beta.assistants.create(
    name="Document Assistant",
    instructions="You are a helpful assistant. Use your knowledge base to answer questions from uploaded documents.",
    model="gpt-4o",
    tools=[{"type": "file_search"}],
)

print("Assistant created:", assistant.id)