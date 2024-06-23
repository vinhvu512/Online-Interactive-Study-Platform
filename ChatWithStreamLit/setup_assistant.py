import openai
from openai import OpenAI
import os

client = OpenAI(api_key="sk-proj-YwBoraiCYxQkLrxAY4SeT3BlbkFJyANuw6SIWHZ4F9AxmgCi")

assistant = client.beta.assistants.create(
    name="Document Assistant",
    instructions="You are a helpful assistant. Use your knowledge base to answer questions from uploaded documents.",
    model="gpt-4o",
    tools=[{"type": "file_search"}],
)

print("Assistant created:", assistant.id)