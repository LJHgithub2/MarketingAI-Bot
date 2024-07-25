import os
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_community.document_loaders import UnstructuredPowerPointLoader
from dotenv import load_dotenv
import re
from pathlib import Path
import pandas as pd
from collections import defaultdict
from langchain_core.documents import Document

# BASE_DIR은 Django 프로젝트의 루트 디렉토리를 나타냅니다.
BASE_DIR = Path(__file__).resolve().parent

# .env 파일 경로 설정
dotenv_path = BASE_DIR / 'env' / '.env'
load_dotenv(dotenv_path)

# 필요한 환경 변수 가져오기
GPT_API_KEY = os.getenv('GPT_API_KEY')
CSV_FILE_PATH = BASE_DIR / 'env' / 'data_v2.csv'
PPTX_FILE_PATH = BASE_DIR / 'env' / 'data.pptx'

print(f"Loading CSV file from: {CSV_FILE_PATH}")
print(f"Loading PPTX file from: {PPTX_FILE_PATH}")

# 경로 확인
if not CSV_FILE_PATH.exists():
    raise FileNotFoundError(f"File not found: {CSV_FILE_PATH}")
# 경로 확인
if not PPTX_FILE_PATH.exists():
    raise FileNotFoundError(f"File not found: {PPTX_FILE_PATH}")
      
filtered_file_path = "./filtered_output.csv"

# pandas를 사용하여 CSV 파일 로드
df = pd.read_csv(CSV_FILE_PATH)

# 해쉬태그 컬럼에서 '#이벤트' 또는 '#EVENT'를 포함하는 행 필터링
df_filtered = df[~df['해쉬태그'].str.contains('#이벤트|#EVENT', case=False, na=False)]

# 필터링된 데이터를 임시 CSV 파일로 저장
df_filtered.to_csv(filtered_file_path, index=False)
# CSV 데이터 로드
loader = CSVLoader(file_path=filtered_file_path,
                   encoding = 'UTF-8')
data1 = loader.load()
print(PPTX_FILE_PATH)
loader = UnstructuredPowerPointLoader(
    str(PPTX_FILE_PATH), mode="elements"
)
load_item = loader.load()

grouped_documents = defaultdict(list)
for doc in load_item:
    if 'page_number' in doc.metadata:
      page_number = doc.metadata['page_number']
      grouped_documents[page_number].append(doc)

# 페이지 번호별로 결합된 Document 생성
combined_documents=[]
for page_number, docs in grouped_documents.items():
    combined_content = "\n".join([doc.page_content for doc in docs])
    combined_metadata = docs[0].metadata  # 첫 문서의 메타데이터 사용
    
    document = Document(
        page_content=combined_content,
        metadata=combined_metadata
    )
    combined_documents.append(document)

data2 = []
for doc in combined_documents:
    if doc.page_content.startswith("Product"):
        data2.append(doc)

# OpenAI 임베딩 설정
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=GPT_API_KEY)

# SNS_FAISS 벡터스토어 설정
vectorstore_SNS = FAISS.from_documents(data1, embeddings)

# info_FAISS 벡터스토어 설정
vectorstore_info = FAISS.from_documents(data2, embeddings)

# 리트리버 설정
retriever_SNS = vectorstore_SNS.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.5, "k": 5},
)

# 리트리버 설정
retriever_info = vectorstore_info.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.5, "k": 3},
)


template = """
You are an assistant for writing marketing promotional content. Use the provided product description and promotional example to answer the question. If you don’t know the answer, simply say that you don’t know. Keep your answer to no more than four sentences.

Question: {question}
Promotional Example: {context}
Product Information: {context2}
Answer:
Create a promotional message based on the product description and use the tone of the promotional example to craft your response.
"""

# 프롬프트 템플릿 불러오기
prompt = hub.pull("rlm/rag-prompt")
# 프롬프트 내용 추가 (말투 동기화)
additional_content = "\nPlease ensure to provide detailed references and explanations in a concise manner."
prompt.messages[0].prompt.template =template
prompt.input_variables.append('context2')

# llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=GPT_API_KEY)
llm = ChatOpenAI(model="gpt-4-turbo",openai_api_key=GPT_API_KEY)

def format_docs(docs):
    result = []
    for doc in docs:
        page_content = doc.page_content
        result.append(page_content)
    return "\n\n".join(result)

# 홍보글 예시 문서를 json형식으로 변환
def sns_convert_to_json(string):
    # 문자열에서 각 요소를 추출하는 정규식 패턴
    pattern = r"Index: (\d+)\n생성시간: ([\d.:\s]+)\n게시글내용: ([^\n]+)\n해쉬태그: \[([^\]]+)\]\nimg_path: ([^\n]+)"
    match = re.search(pattern, string)

    if not match:
        raise ValueError("String format is incorrect")

    index = int(match.group(1))
    생성시간 = match.group(2)
    게시글내용 = match.group(3)
    해쉬태그 = match.group(4).replace("'", "").split(", ")
    img_path = match.group(5).replace("\\", "/")

    # JSON 객체 생성
    json_data = {
        "Index": index,
        "생성시간": 생성시간,
        "게시글내용": 게시글내용,
        "해쉬태그": 해쉬태그,
        "img_path": img_path
    }
    return json_data

# 제품 정보문서를 json형식으로 변환
def info_convert_to_json(string,page_number):

    # JSON 객체 생성
    json_data = {
        "제품 정보": string,
        "페이지 번호": page_number,
    }
    return json_data


def generate_promotion(query):
    try:
        docs_sns = retriever_SNS.invoke(query)
        docs_info = retriever_info.invoke(query)

        prompt_result = prompt.format(context=format_docs(docs_sns),context2=format_docs(docs_info), question=query)

        result = llm(prompt_result)

        arr_sns= []
        arr_info= []
        for doc in docs_sns:
            arr_sns.append(sns_convert_to_json(doc.page_content))
        for doc in docs_info:
            arr_info.append(info_convert_to_json(doc.page_content,doc.metadata['page_number']))
        response_data = {
            "section1":arr_sns, # 홍보글
            "section2":result.content,# 결과
            "section3":arr_info, # 제품정보
        }
        return response_data
    
    except Exception as e:
        print(e)
        return False
