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
        doc_path = os.path.join(base_dir, "실무보감_전철전력.md") # 전체 원본 문서로 교체
        
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

st.title("🚆 KORAIL AX - 통합 플랫폼 PoC")

tab1, tab2 = st.tabs(["📑 공통업무 AI (RAG)", "📐 설계업무 AI (CAD 최적화)"])

with tab1:
    st.markdown("### **'전철전력 실무보감'** (Upstage Solar Pro LLM)")
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

with tab2:
    st.markdown("### 🔌 변전설비 2D 자동 최적 배치기")
    st.markdown("AI(OR-Tools)가 **이격거리 규정**과 **겹침 방지** 제약을 준수하여 설비 패킹 좌표를 선출합니다.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**[시뮬레이션 공간 규격]**")
        space_width = st.slider("가로 (Width, m)", 30, 80, 45, 5)
        space_height = st.slider("세로 (Height, m)", 30, 80, 35, 5)
    
        st.markdown("**[최적화 대상 모델]**")
        st.code('''[
  {"name": "M_TR_150MVA", "w": 8, "h": 10, "clearance": 3},
  {"name": "GIS_170kV", "w": 12, "h": 6, "clearance": 2},
  {"name": "SWG_25.8kV", "w": 15, "h": 5, "clearance": 2},
  {"name": "Condenser", "w": 5, "h": 5, "clearance": 1},
  {"name": "ESS_Battery", "w": 10, "h": 8, "clearance": 2},
  {"name": "Control_Panel", "w": 6, "h": 3, "clearance": 1}
]''', language='json')
        
    with col2:
        if st.button("🚀 AI 레이아웃 최적화 연산", type="primary"):
            from design_ai_poc import optimize_layout, generate_cad_dxf
            
            equipment_specs = [
                {"name": "M_TR_150MVA", "width": 8, "height": 10, "clearance": 3},
                {"name": "GIS_170kV", "width": 12, "height": 6, "clearance": 2},
                {"name": "SWG_25.8kV", "width": 15, "height": 5, "clearance": 2},
                {"name": "Condenser", "width": 5, "height": 5, "clearance": 1},
                {"name": "ESS_Battery", "width": 10, "height": 8, "clearance": 2},
                {"name": "Control_Panel", "width": 6, "height": 3, "clearance": 1}
            ]
            
            with st.spinner("SAT Solver 교차 검증 연산 중..."):
                layout_result = optimize_layout(equipment_specs, space_width, space_height)
            
            if layout_result:
                st.success(f"🎯 최적 좌표 도출 완료 (공간: {space_width}x{space_height})")
                
                # DXF 파일 생성 연동
                output_dxf = "substation_layout.dxf"
                if generate_cad_dxf(layout_result, output_dxf):
                    import pandas as pd
                    df = pd.DataFrame(layout_result)
                    st.dataframe(df.set_index("name"), use_container_width=True)
                    
                    with open(output_dxf, "rb") as file:
                        st.download_button(
                            label="📄 2D CAD (DXF) 결과 다운로드",
                            data=file,
                            file_name="optimized_substation.dxf",
                            mime="application/dxf",
                        )
                else:
                    st.error("CAD 도면 생성 라이브러리 연동 실패")
            else:
                st.error(f"❌ 실패: 입력하신 면적({space_width}x{space_height}) 내에서는 해당 설비들을 안전거리 규정에 맞게 모두 배치할 수 없습니다. 공간(가로/세로)을 더 넓혀주세요.")
