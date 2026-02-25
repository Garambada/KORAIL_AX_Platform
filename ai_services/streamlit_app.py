import streamlit as st
import os
import requests
import json
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate

# Set API Key securely in environment
os.environ["UPSTAGE_API_KEY"] = "up_mK2h7yONqSmhFo8WfFIsr35B1hy83"

st.set_page_config(page_title="KORAIL AX - 공통업무 AI (Powered by Solar Pro)", page_icon="🚆", layout="centered")

@st.cache_resource(show_spinner=False)
def load_rag_engine():
    try:
        # Streamlit Cloud 경로 문제 해결을 위해 절대 경로 확보
        base_dir = os.path.dirname(os.path.abspath(__file__))
        doc_path = os.path.join(base_dir, "실무보감_전철전력_요약.md")
        
        if not os.path.exists(doc_path):
            st.error(f"오류: 문서를 찾을 수 없습니다. 경로: {doc_path}")
            return None
            
        # 1. 로드
        loader = TextLoader(doc_path, encoding="utf-8")
        docs = loader.load()
        # 2. 청크 분할
        splitter = MarkdownTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        # 3. 임베딩 및 인덱싱
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(chunks, embeddings)
        return vectorstore
    except Exception as e:
        import traceback
        st.error(f"지식 베이스 로딩 중 치명적 오류 발생:\n{traceback.format_exc()}")
        return None

def generate_solar_response(context: str, query: str) -> str:
    """Upstage Solar Pro API를 호출하여 자연어 답변을 생성합니다."""
    url = "https://api.upstage.ai/v1/solar/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['UPSTAGE_API_KEY']}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""당신은 한국철도공사(KORAIL) 전철전력 전문가이자 AI 어시스턴트입니다.
반드시 제공된 [참조 내용]만을 근거로 사용자의 [질문]에 상세하고 친절하게 답변해주세요.
참조 내용에 해당하는 정보가 없다면 "제공된 문서(실무보감)에서는 해당 내용을 찾을 수 없습니다."라고 솔직하게 답변하세요.

[참조 내용]
{context}

[질문]
{query}
"""
    
    data = {
        "model": "solar-pro",
        "messages": [
            {"role": "system", "content": "You are a helpful KORAIL railway electricity expert assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1 # 전문적이고 사실 지향적인 답변을 위해 낮음
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Raise exception for bad status codes
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Solar Pro LLM 호출 중 에러가 발생했습니다: {str(e)}"

st.title("🚆 KORAIL AX - 공통업무 AI")
st.markdown("**'전철전력 실무보감'** (Upstage Solar Pro LLM)")

with st.spinner("🧠 실무보감 지식 베이스(Vector DB)를 로딩 중입니다..."):
    vectorstore = load_rag_engine()
    
if vectorstore:
    st.success("✅ 실무보감 지식 베이스 로딩 완료!")
else:
    st.warning("⚠️ 지식 베이스를 로딩하지 못했습니다.")

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 초기 안내 메시지
    st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! Upstage Solar 기반 실무보감 어시스턴트입니다. 규정, 계약 등 어떤 것이든 물어보세요.\n\n*(예시: 설계변경 관리는 언제, 어떻게 해야 해?)*"})

# 이전 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요..."):
    # 사용자 메시지 추가 및 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # AI 답변 처리
    with st.chat_message("assistant"):
        with st.spinner("지식 검색 및 답변 생성 중 (Solar Pro)..."):
            if vectorstore:
                # 1. 문서 검색 (Retrieval)
                results = vectorstore.similarity_search(prompt, k=3)
                if results:
                    context = "\n\n".join([r.page_content for r in results])
                    
                    # 2. LLM 생성 (Generation)
                    answer = generate_solar_response(context, prompt)
                    
                    # 3. 출처 표기 추가
                    answer += "\n\n---\n*🔍 [검색된 참조 출처 요약]*\n"
                    for idx, r in enumerate(results):
                        snippet = r.page_content.replace('\n', ' ')[:100] + "..."
                        answer += f"<small>**[{idx+1}]** {snippet}</small>\n\n"
                        
                else:
                    answer = "해당하는 내용을 실무보감에서 찾을 수 없습니다."
            else:
                answer = "지식 베이스가 오류로 인해 로드되지 않았습니다."
                
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
