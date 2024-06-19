import streamlit as st
import openai
from openai import OpenAI

client = OpenAI(api_key="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")

assistant_id = "asst_V91MJ0qJsnrLXpn4x9657GB5"
vector_store_id = "vs_myBsbclDk12fPCUkPwVcEczs"
thread_id = "thread_d0ButYPxMTycoie4SQHsOdkn"

def search_files(thread_id, query):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role='user',
        content=query,
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    messages = list(client.beta.threads.messages.list(thread_id=thread_id, run_id=run.id))
    message_content = messages[0].content[0].text
    return message_content

def send_message_to_gpt4(query):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query},
        ]
    )
    return response.choices[0].message.content

def explain_incorrect_answers(answers):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Explain the following incorrect answers:\n\n{answers}"}
        ],
        max_tokens=150
    )
    return response.choices[0].message.content

st.title("Interactive Learning Platform")
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'query_mode' not in st.session_state:
    st.session_state['query_mode'] = 'chat'  # Default to chat mode

# Tab selection
tab = st.radio("Choose Mode", ('Chat with GPT-4', 'Document Search'))

def send_message():
    query = st.session_state['input']
    if st.session_state['query_mode'] == 'document_search':
        st.session_state['messages'].append(f"User (document search): {query}")
        results = search_files(thread_id, query)
        st.session_state['messages'].append(f"Document search results: {results}")
    else:
        st.session_state['messages'].append(f"User: {query}")
        response = send_message_to_gpt4(query)
        st.session_state['messages'].append(f"GPT-4: {response}")
    st.session_state['input'] = ""

st.text_input("Enter your query or answers:", key="input", on_change=send_message)

if tab == 'Chat with GPT-4':
    st.session_state['query_mode'] = 'chat'
    st.write("Mode: Chat with GPT-4")
    for message in st.session_state['messages']:
        if message.startswith("User:") or message.startswith("GPT-4:"):
            st.write(message)

elif tab == 'Document Search':
    st.session_state['query_mode'] = 'document_search'
    st.write("Mode: Document Search")
    for message in st.session_state['messages']:
        if message.startswith("User (document search):") or message.startswith("Document search results:"):
            st.write(message)


def check_answer_with_gpt4(question, answer):
    query = f"Question: {question}\nAnswer: {answer}\nIs this answer correct? If not, explain why."
    explanation = send_message_to_gpt4(query)
    return explanation
st.title("Lecture Questions")

if 'questions' not in st.session_state:
    st.session_state['questions'] = []

if st.button("Load Questions"):
    questions = [
        {"question": "What is the key takeaway from the first section?", "answer": ""},
        {"question": "Explain how CNNs are different from RNNs.", "answer": ""}
    ]
    st.session_state['questions'] = questions

if st.session_state['questions']:
    questions = st.session_state['questions']
    for i, q in enumerate(questions):
        st.write(f"Question {i+1}: {q['question']}")
        q['answer'] = st.text_area(f"Your Answer {i+1}", q['answer'], key=f"answer_{i}")

    if st.button("Submit Answers"):
        explanations = []
        for q in questions:
            explanation = check_answer_with_gpt4(q['question'], q['answer'])
            explanations.append(explanation)

        for i, explanation in enumerate(explanations):
            st.write(f"Explanation for Question {i+1}: {explanation}")