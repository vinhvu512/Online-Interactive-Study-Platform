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
        return json.dumps({"arxiv_results": papers}, indent=2)
    else:
        return json.dumps({"arxiv_results": []}, indent=2)

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
    
    return json.dumps({"multiple_choice_questions": questions}, indent=2)

# Main execution
with open('/Users/twang/Downloads/tes_folder_for_bki/after_batch_4.txt', 'r') as file:
    file_loaded = file.read()

print("File Content:")
print(file_loaded[:500] + "...")  # Print first 500 characters
print("\n" + "="*50 + "\n")

main_topics = generate_main_content(file_loaded)
print("Main Topics:")
print(main_topics)
print("\n" + "="*50 + "\n")

arxiv_results_json = search_arxiv(main_topics, max_results=3)
print("arXiv Search Results (JSON format):")
print(arxiv_results_json)
print("\n" + "="*50 + "\n")

mc_questions_json = generate_multiple_choice(file_loaded)
print("Multiple Choice Questions (JSON format):")
print(mc_questions_json)
print("\n" + "="*50 + "\n")