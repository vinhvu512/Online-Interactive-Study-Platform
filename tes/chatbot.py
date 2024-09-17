import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage,Document
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI
import chainlit as cl
import dotenv
import time
dotenv.load_dotenv()

# Initialize LLM
llm = OpenAI(model="gpt-4o-mini")

# Đường dẫn lưu trữ index
PERSIST_DIR = "./storage"

@cl.on_chat_start
async def start():
    content_folder = os.path.join(os.path.dirname(__file__), "..", "media", "generated_contents")
    if not os.path.exists(content_folder):
        raise FileNotFoundError(f"The folder {content_folder} does not exist.")
    
    print(f"Reading files from: {content_folder}")
    
    # Kiểm tra xem index đã tồn tại chưa
    if os.path.exists(PERSIST_DIR):
        # Nếu có, load index từ storage
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)
        print("Loaded existing index from storage")
        
        # Kiểm tra và thêm tài liệu mới (nếu có)
        all_files = set(f for f in os.listdir(content_folder) if os.path.isfile(os.path.join(content_folder, f)))
        indexed_files = set(os.path.basename(doc_id) for doc_id in index.docstore.docs.keys())
        new_files = all_files - indexed_files
        
        if new_files:
            print(f"Found {len(new_files)} new documents")
            new_documents = []
            for file in new_files:
                file_path = os.path.join(content_folder, file)
                if os.path.exists(file_path):
                    try:
                        # Sử dụng SimpleDirectoryReader để đọc file
                        reader = SimpleDirectoryReader(input_files=[file_path])
                        docs = reader.load_data()
                        new_documents.extend(docs)
                    except Exception as e:
                        print(f"Error reading file {file}: {str(e)}")
            
            if new_documents:
                print(f"Adding {len(new_documents)} new documents to the index")
                # Convert documents to nodes
                nodes = index.storage_context.docstore.add_documents(new_documents)
                if nodes:  # Kiểm tra xem nodes có tồn tại không
                    # Insert nodes into the index
                    index.insert_nodes(nodes)
                    index.storage_context.persist(persist_dir=PERSIST_DIR)
                    print("Updated index saved to storage")
                else:
                    print("No nodes were created from the new documents")
            else:
                print("No new documents were successfully read")
    else:
        # Nếu chưa, tạo index mới
        documents = SimpleDirectoryReader(content_folder).load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=PERSIST_DIR)
        print("Created new index and saved to storage")
    
    # Tạo query engine
    query_engine = index.as_query_engine()
    
    # Tạo tool cho agent
    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="content_knowledge",
            description="Useful for answering questions based on the content of all files in the specified folder"
        )
    )
    
    # Khởi tạo agent với tool
    agent = ReActAgent.from_tools([query_engine_tool], llm=llm, verbose=True)
    
    cl.user_session.set("agent", agent)
    cl.user_session.set("index", index)
    cl.user_session.set("content_folder", content_folder)
    cl.user_session.set("last_update_time", time.time())

@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    index = cl.user_session.get("index")
    content_folder = cl.user_session.get("content_folder")
    
    # Kiểm tra và thêm tài liệu mới (nếu có)
    new_documents = SimpleDirectoryReader(content_folder).load_data()
    if new_documents:
        print("Adding new documents to the index")
        index.insert_nodes(new_documents)
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    
    response = await agent.aquery(message.content)
    await cl.Message(content=response.response).send()

if __name__ == "__main__":
    cl.run()
