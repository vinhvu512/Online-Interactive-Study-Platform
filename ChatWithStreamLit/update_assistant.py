from openai import OpenAI
import os


client = OpenAI(api_key="sk-proj-YwBoraiCYxQkLrxAY4SeT3BlbkFJyANuw6SIWHZ4F9AxmgCi")

assistant_id = "asst_V91MJ0qJsnrLXpn4x9657GB5"

# vector_store = client.beta.vector_stores.create(name="DocumentSearch")
# print(f"Vector Store Id - {vector_store.id}")
vector_store_id = "vs_myBsbclDk12fPCUkPwVcEczs"
file_path = ['/Users/vinhvu/LMS/ChatWithStreamLit/file_test/demo1.pdf','/Users/vinhvu/LMS/ChatWithStreamLit/file_test/demo2.pdf']
file_streams = [open(path,"rb") for path in file_path]

file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store_id,
    files=file_streams
)
print(f"File Status: {file_batch.status}")

assistant = client.beta.assistants.update(
    assistant_id=assistant_id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},

)
print("Assistant Updated with Vector Store")

# thread = client.beta.threads.create()
thread_id = "thread_d0ButYPxMTycoie4SQHsOdkn"
# thread_id = thread['id']
# print(f"Your thread id is - {thread}\n\n")
print(f"Your thread id is - {thread_id}\n\n")

while True:
    text = input("What's your question? ")

    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role='user',
        content=text,
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    messages = list(client.beta.threads.messages.list(thread_id=thread_id, run_id=run.id))
    message_content = messages[0].content[0].text
    print("Response: \n")
    print(message_content)