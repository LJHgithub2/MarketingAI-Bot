import os
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain import hub
from dotenv import load_dotenv
import re
from pathlib import Path
import pandas as pd

# BASE_DIR은 Django 프로젝트의 루트 디렉토리를 나타냅니다.
BASE_DIR = Path(__file__).resolve().parent

# .env 파일 경로 설정
dotenv_path = BASE_DIR / 'env' / '.env'
load_dotenv(dotenv_path)

# 필요한 환경 변수 가져오기
GPT_API_KEY = os.getenv('GPT_API_KEY')
CSV_FILE_PATH = BASE_DIR / 'env' / 'data.csv'

print(f"Loading CSV file from: {CSV_FILE_PATH}")

# 경로 확인
if not CSV_FILE_PATH.exists():
    raise FileNotFoundError(f"File not found: {CSV_FILE_PATH}")
      
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
data = loader.load()

# OpenAI 임베딩 설정
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=GPT_API_KEY)

# FAISS 벡터스토어 설정
vectorstore = FAISS.from_documents(data, embeddings)

# 리트리버 설정
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.5, "k": 7},
)

# 프롬프트 템플릿 불러오기
prompt = hub.pull("rlm/rag-prompt")
# 프롬프트 내용 추가 (말투 동기화)
additional_content = "\nPlease ensure to provide detailed references and explanations in a concise manner."
prompt.messages[0].prompt.template += additional_content

# llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=GPT_API_KEY)
llm = ChatOpenAI(model="gpt-4-turbo",openai_api_key=GPT_API_KEY)

def format_docs(docs):
    result = []
    for doc in docs:
        page_content = doc.page_content
        result.append(page_content)
    return "\n\n".join(result)

def convert_to_json(string):
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

def generate_promotion(query):
    try:
        docs = retriever.invoke(query)

        result = prompt.format(context=format_docs(docs), question=query)

        result = llm(result)

        arr= []
        for doc in docs:
            arr.append(convert_to_json(doc.page_content))
        response_data = {"section1":arr,"section2":result.content}
        return response_data
    except Exception as e:
        print(e)
        return False
