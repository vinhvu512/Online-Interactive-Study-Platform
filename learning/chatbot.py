import os
import shutil
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.llms.openai import OpenAI
import chainlit as cl
import dotenv
import time

dotenv.load_dotenv()

# Single LLM for retriever + synthesis (ReActAgent.from_tools was removed in newer LlamaIndex)
llm = OpenAI(model="gpt-4o-mini")
Settings.llm = llm

# Đường dẫn lưu trữ index
PERSIST_DIR = "./storage"

@cl.on_chat_start
async def start():
    content_folder = os.path.join(os.path.dirname(__file__), "..", "media", "generated_contents")
    if not os.path.exists(content_folder):
        raise FileNotFoundError(f"The folder {content_folder} does not exist.")
    
    print(f"Reading files from: {content_folder}")
    
    index = None
    has_persisted = os.path.isdir(PERSIST_DIR) and bool(os.listdir(PERSIST_DIR))

    if has_persisted:
        try:
            storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
            index = load_index_from_storage(storage_context)
            # Touch docstore: old saves used __type__/__data__ without class_name; new LlamaIndex raises KeyError.
            list(index.docstore.docs.keys())
            print("Loaded existing index from storage")
        except Exception as e:
            print(
                f"LlamaIndex storage is missing/incompatible with this version ({e!r}); rebuilding from {content_folder}."
            )
            shutil.rmtree(PERSIST_DIR, ignore_errors=True)
            index = None

    if index is None:
        documents = SimpleDirectoryReader(content_folder).load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=PERSIST_DIR)
        print("Created new index and saved to storage")
    else:
        # Compare disk files to ingested ref docs (docstore node IDs are UUIDs, not filenames)
        all_files = {
            f
            for f in os.listdir(content_folder)
            if os.path.isfile(os.path.join(content_folder, f))
        }
        ref_map = index.docstore.get_all_ref_doc_info() or {}
        if not ref_map:
            print("No ref_doc_info on index; skipping incremental file scan (avoids duplicate inserts).")
        else:
            indexed_basenames = set()
            for ref_id, info in ref_map.items():
                meta = getattr(info, "metadata", None) or {}
                path_hint = meta.get("file_path") or meta.get("file_name") or ref_id
                indexed_basenames.add(os.path.basename(str(path_hint)))

            new_files = all_files - indexed_basenames
            if new_files:
                print(f"Found {len(new_files)} new documents")
                added = 0
                for file in new_files:
                    file_path = os.path.join(content_folder, file)
                    try:
                        reader = SimpleDirectoryReader(input_files=[file_path])
                        for doc in reader.load_data():
                            index.insert(doc)
                            added += 1
                    except Exception as e:
                        print(f"Error reading file {file}: {e}")
                if added:
                    index.storage_context.persist(persist_dir=PERSIST_DIR)
                    print(f"Updated index with {added} document(s), saved to storage")

    query_engine = index.as_query_engine(llm=llm)

    cl.user_session.set("query_engine", query_engine)
    cl.user_session.set("index", index)
    cl.user_session.set("content_folder", content_folder)
    cl.user_session.set("last_update_time", time.time())

@cl.on_message
async def main(message: cl.Message):
    query_engine = cl.user_session.get("query_engine")
    response = await query_engine.aquery(message.content)
    text = response.response if getattr(response, "response", None) else str(response)
    await cl.Message(content=text or "(empty response)").send()

if __name__ == "__main__":
    cl.run()
