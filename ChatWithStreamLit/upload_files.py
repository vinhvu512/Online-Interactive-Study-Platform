from openai import OpenAI
import os

client = OpenAI(api_key="sk-proj-YwBoraiCYxQkLrxAY4SeT3BlbkFJyANuw6SIWHZ4F9AxmgCi")

# Tạo vector store
vector_store = client.beta.vector_stores.create(name="Document Store")

# Đường dẫn đến các tài liệu
file_paths = ["/Users/twang/PycharmProjects/LMS-file/ChatWithStreamLit/file_test/demo1.pdf", "/Users/twang/PycharmProjects/LMS-file/ChatWithStreamLit/file_test/demo2.pdf"]

# Tải các tài liệu lên và thêm chúng vào vector store
file_streams = [open(path, "rb") for path in file_paths]
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id, files=file_streams
)

print("Vector Store ID:", vector_store.id)
print("File Batch Status:", file_batch.status)
print("File Counts:", file_batch.file_counts)