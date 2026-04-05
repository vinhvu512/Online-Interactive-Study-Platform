import requests
import xml.etree.ElementTree as ET
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def search_arxiv(query, max_results=5):
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        root = ET.fromstring(response.content)
        papers = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title").text
            link = entry.find("{http://www.w3.org/2005/Atom}id").text
            papers.append({"title": title, "link": link})
        return {"arxiv_results": papers}
    else:
        return {"arxiv_results": []}

def generate_main_content(file_content):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert at identifying 3 key topics in text."},
            {"role": "user", "content": f"Don't give me list, give me single string.Analyze the following content and give me main keyword topics, Give me in one line, seperate by comma, dont give me list, normal string.:\n\n{file_content}"}
        ],
        max_tokens=100,
        temperature=0.7,
    )
    
    topics = response.choices[0].message.content.strip()
    return topics

def generate_multiple_choice(context):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates multiple-choice questions."},
            {"role": "user", "content": f"""Generate 3 multiple-choice questions based on this content. Each question should have 4 options. Provide the answer as the index (0-3) of the correct option. Use the following XML format strictly:

<question>Question text here</question>
<option>Option 1</option>
<option>Option 2</option>
<option>Option 3</option>
<option>Option 4</option>
<answer>Correct answer index (0-3)</answer>

Content: {context}"""}
        ],
        max_tokens=2048,
        temperature=0.7,
    )
    
    # Parse the XML response
    xml_string = "<root>" + response.choices[0].message.content.strip() + "</root>"
    root = ET.fromstring(xml_string)
    
    questions = []
    for i in range(0, len(root), 6):  # Each question has 6 elements
        question = {
            "question": root[i].text,
            "options": [root[i+1].text, root[i+2].text, root[i+3].text, root[i+4].text],
            "answer": int(root[i+5].text)
        }
        questions.append(question)
    
    return {"multiple_choice_questions": questions}

def generate_summary(context):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes content."},
            {"role": "user", "content": f"Summarize the following content:\n\n{context}"}
        ],
        max_tokens=150,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()



