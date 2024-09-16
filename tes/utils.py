import requests
import xml.etree.ElementTree as ET
from openai import OpenAI
from dotenv import load_dotenv
import os
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
        return papers
    else:
        return []

# # Demo: Search for papers about RAG
# papers = search_arxiv("Paper about Transformer", max_results=1)
# print(papers)
# for i, paper in enumerate(papers):
#     print(f"{i+1}. {paper['title']}")
#     print(f"   Link: {paper['link']}")
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

def generate_multiple_choice(context):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates multiple-choice questions."},
            {"role": "user", "content": f"Generate 3 multiple-choice questions based on this content:\n\n{context}"}
        ],
        max_tokens=300,
        temperature=0.7,
    )
    
    # Parse the response and format it as a list of dictionaries
    questions_text = response.choices[0].message.content.strip()
    questions = questions_text.split('\n\n')
    formatted_questions = []
    for q in questions:
        lines = q.split('\n')
        question = lines[0]
        options = lines[1:-1]
        answer = lines[-1].replace('Answer: ', '')
        formatted_questions.append({
            'question': question,
            'options': options,
            'answer': answer
        })
    return formatted_questions


