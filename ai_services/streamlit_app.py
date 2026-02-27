import streamlit as st
import os
import time
import requests
import json
import pydeck as pdk
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from langchain_community.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader
from langchain_text_splitters import MarkdownTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate

# Set API Key securely in environment
os.environ["UPSTAGE_API_KEY"] = "up_mK2h7yONqSmhFo8WfFIsr35B1hy83"

st.set_page_config(page_title="KRNA AX - 공통업무 AI (Powered by Solar Pro)", page_icon="🚆", layout="centered")

# Custom UI Styling (Professional GUI & Scrollable Container)
st.markdown("""
<style>
    /* Hide main scrollbar and constrain height */
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
        height: 100vh;
        margin: 0;
        padding: 0;
        background-color: #f8f9fa !important;
    }
    
    /* Make the workspace scrollable instead of the page */
    [data-testid="stMainBlockContainer"] {
        overflow-y: auto !important;
        height: calc(100vh - 150px) !important;
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }
    
    /* Global Text Color Fix for Light Mode */
    p, span, div, li, strong, em {
        color: #1e1e1e !important;
    }
    
    /* Professional Typography and Accent Colors */
    h1, h2, h3 {
        color: #0E4B75 !important; /* KRNA Blue */
        font-family: 'Helvetica Neue', Arial, sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Chat message container refinements */
    [data-testid="stChatMessage"] {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ffffff !important;
        border: 1px solid #dee2e6 !important;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Make the main tab buttons larger and more prominent */
    [data-baseweb="tab"] {
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        background-color: transparent !important;
    }
    
    button[data-baseweb="tab"] p {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #495057 !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #0E4B75 !important;
    }
    
    /* Input box floating at bottom */
    [data-testid="stBottom"] {
        background-color: white !important;
        border-top: 1px solid #e9ecef;
    }
    
    /* Visible Custom Scrollbar for Mac/Windows */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1; 
        border-radius: 8px;
    }
    ::-webkit-scrollbar-thumb {
        background: #0E4B75; 
        border-radius: 8px;
        border: 2px solid #f1f1f1;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #0a3654; 
    }
    
    /* Force Light Theme on Expanders, Popups, and Inputs */
    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 0.5rem !important;
    }
    [data-testid="stExpander"] details summary p {
        color: #0E4B75 !important;
        font-weight: 700 !important;
    }
    [data-testid="stExpander"] details {
        background-color: #ffffff !important;
    }
    
    /* Force Light Theme on Input Widgets (Sliders, Text Inputs, Buttons) */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div, 
    div[data-baseweb="base-input"],
    .stTextInput input, 
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #1e1e1e !important;
        -webkit-text-fill-color: #1e1e1e !important;
    }
    
    /* Ensure markdown and regular text outside containers are also dark */
    .stMarkdown p, .stMarkdown span {
        color: #1e1e1e !important;
    }
    
    /* Force Light Theme on info/success/warning boxes */
    [data-testid="stAlert"] {
        background-color: #f8f9fa !important;
        color: #1e1e1e !important;
    }
    
    /* Ensure code blocks stay readable */
    code {
        color: #d63384 !important;
        background-color: #f8f9fa !important;
    }
    pre code {
        color: #212529 !important;
        background-color: transparent !important;
    }
    div[data-testid="stCodeBlock"] {
        background-color: #f8f9fa !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
def load_rag_engine():
    try:
        # Streamlit Cloud 경로 문제 해결을 위해 절대 경로 확보
        base_dir = os.path.dirname(os.path.abspath(__file__))
        doc_path = os.path.join(base_dir, "data_real") # 실제 법령 데이터 폴더로 교체
        
        if not os.path.exists(doc_path):
            st.error(f"오류: 문서 폴더를 찾을 수 없습니다. 경로: {doc_path}")
            return None
            
        # 1. 로드 (PDF 디렉토리 로더 사용)
        pdf_loader = DirectoryLoader(doc_path, glob="**/*.pdf", loader_cls=PyPDFLoader)
        docs = pdf_loader.load()
        
        # 2. 청크 분할 (PDF용 텍스트 분할기 사용)
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
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
참조 내용에 해당하는 정보가 없다면 "제공된 문서(법령/내규)에서는 해당 내용을 찾을 수 없습니다."라고 솔직하게 답변하세요.

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

st.title("🚆 KRNA 전철전력 설계·시공 통합 AI 플랫폼")
st.markdown("**Powered by Upstage Solar Pro3** | 📄 RAG 문서 대화 & 📐 AI 자동 설계 도면 생성")

tab1, tab2 = st.tabs(["공통업무 AI (RAG)", "설계업무 AI (CAD 최적화)"])

with tab1:
    st.markdown("### **'전철전력 실무보감'** (Upstage Solar Pro LLM)")
    with st.spinner("🧠 실무보감 지식 베이스(Vector DB)를 로딩 중입니다..."):
        vectorstore = load_rag_engine()
        
    if vectorstore:
        st.toast("✅ 실무보감 지식 베이스 로딩 완료!")
    else:
        st.warning("⚠️ 지식 베이스를 로딩하지 못했습니다.")
    
    # 대화 기록 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # 초기 안내 메시지
        st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! Upstage Solar 기반 법령/내규 챗봇 어시스턴트입니다. 규정, 계약 등 어떤 것이든 물어보세요.\n\n*(예시: 전기안전관리자의 직무는 어떻게 되나요?)*"})
    
    # 이전 대화 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)
    
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
                            source_file = r.metadata.get('source', '알 수 없는 파일').split('/')[-1]
                            page_num = r.metadata.get('page', '알 수 없음')
                            snippet = r.page_content.replace('\n', ' ')[:100] + "..."
                            answer += f"<small>**[{idx+1}] {source_file} (페이지 {page_num})**<br>{snippet}</small>\n\n"
                    else:
                        answer = "해당하는 내용을 제공된 문서에서 찾을 수 없습니다."
                else:
                    answer = "지식 베이스가 오류로 인해 로드되지 않았습니다."
                    
                st.markdown(answer, unsafe_allow_html=True)
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

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 🛠️ KRNA 전철전력 설계업무 AI 확장 로드맵")
    st.info("💡 **아래 5가지 혁신적인 AI 모듈**이 플랫폼 고도화 2단계에서 순차적으로 탑재될 예정입니다.")
    
    with st.expander("🛤️ 송전선로 최적 노선 3D 맵핑 (Transmission Line Optimal Routing)", expanded=True):
        st.write("지형 데이터를 분석하여 환경 영향과 케이블 길이를 최소화하는 최적의 3D 송전 노선을 제안합니다.")
        
        col_route1, col_route2 = st.columns(2)
        with col_route1:
            st.markdown("**출발 변전소 좌표**")
            start_lat = st.number_input("위도 (Start Lat)", value=37.5665, format="%.4f")
            start_lon = st.number_input("경도 (Start Lon)", value=126.9780, format="%.4f")
        with col_route2:
            st.markdown("**도착 변전소 좌표**")
            end_lat = st.number_input("위도 (End Lat)", value=37.5219, format="%.4f")
            end_lon = st.number_input("경도 (End Lon)", value=127.0411, format="%.4f")
            
        if st.button("🚀 3D 노선 최적화 시뮬레이션 실행", key="btn_routing"):
            with st.spinner("AI 지형 데이터 스캔 및 A* (A-Star) 경로 탐색 중..."):
                time.sleep(1.5) # Simulating API call/processing time
                
                # Mocking route data with elevation (Arching effect)
                route_data = pd.DataFrame({
                    "start_lon": [start_lon],
                    "start_lat": [start_lat],
                    "end_lon": [end_lon],
                    "end_lat": [end_lat],
                    "color": [[14, 75, 117, 255]], # KRNA Blue
                })

                view_state = pdk.ViewState(
                    latitude=(start_lat + end_lat) / 2, 
                    longitude=(start_lon + end_lon) / 2, 
                    zoom=11, 
                    pitch=50,
                    bearing=-15
                )

                arc_layer = pdk.Layer(
                    "ArcLayer",
                    data=route_data,
                    get_source_position=["start_lon", "start_lat"],
                    get_target_position=["end_lon", "end_lat"],
                    get_source_color="color",
                    get_target_color="color",
                    auto_highlight=True,
                    width_scale=0.0001,
                    get_width="2",
                    width_min_pixels=3,
                    width_max_pixels=15,
                    getHeight=0.5
                )

                scatter_layer = pdk.Layer(
                    "ScatterplotLayer",
                    pd.DataFrame({
                        "lon": [start_lon, end_lon],
                        "lat": [start_lat, end_lat],
                        "name": ["출발점", "도착점"],
                        "color": [[214, 51, 132], [25, 135, 84]]
                    }),
                    get_position=["lon", "lat"],
                    get_color="color",
                    get_radius=500,
                    pickable=True
                )

                r = pdk.Deck(
                    layers=[arc_layer, scatter_layer], 
                    initial_view_state=view_state, 
                    tooltip={"text": "{name}"},
                    map_style='light' # Use a light map style for better contrast
                )
                
                st.pydeck_chart(r)
                st.success("✅ 지형 단차 및 지장물을 우회하는 최적 경과지 3D 매핑이 완료되었습니다.")
                
                # Show mock metrics
                m1, m2, m3 = st.columns(3)
                m1.metric(label="총 선로 긍장 (Line Length)", value="14.2 km", delta="-1.8 km (단축)")
                m2.metric(label="예상 철탑 기수", value="38 타워", delta="-4 기 (절감)")
                m3.metric(label="공사비 절감액 추정", value="₩ 12.4 억", delta="최적화 효과")
        
    with st.expander("✅ 설계-시공 규격 자동 교차 검증 (Design-Construction Spec Cross-validation)", expanded=False):
        st.write("설계도면(도면, 내역서)과 시공시방서를 비교 분석하여 누락, 불일치, 위반 항목을 자동으로 찾아냅니다.")
        
        uploaded_file = st.file_uploader("시공 내역서 업로드 (Excel/CSV mock)", type=["csv", "xlsx"], key="validation_upload")
        if st.button("🔍 AI 규격 검증 실행", key="btn_validation", type="secondary"):
            with st.spinner("KRNA 표준 시방서 데이터베이스와 교차 대조 중..."):
                time.sleep(2)
                
                # Mock cross-validation results
                mock_data = {
                    "품목명 (Item)": ["170kV GIS", "154kV M.Tr", "25.8kV SWG", "제어 케이블", "접지 단자판"],
                    "설계도서 규격 (Design)": ["정격 2000A / 50kA", "150/200MVA", "정격 1250A", "CVVS 2.0sq x 10C", "구리 100x10x1000L"],
                    "시공내역서 (Construction)": ["정격 2000A / 50kA", "150/200MVA", "정격 600A (불일치)", "CVVS 1.5sq x 10C (미달)", "누락"],
                    "검증 결과 (Status)": ["PASS", "PASS", "FAIL", "FAIL", "MISSING"]
                }
                
                df_val = pd.DataFrame(mock_data)
                
                def highlight_status(val):
                    color = ''
                    if val == 'FAIL': color = '#ffcccb'
                    elif val == 'MISSING': color = '#ffebee'
                    return f'background-color: {color}'
                    
                st.dataframe(df_val.style.map(highlight_status, subset=['검증 결과 (Status)']), use_container_width=True)
                
                st.error("⚠️ 경고: 시공 내역서와 설계 규격 간 3건의 불일치/누락 항목이 발견되었습니다. (상세 리포트 다운로드 가능)")
        
    with st.expander("🏛️ 내진 설계 안전성 AI 시뮬레이터 (Seismic Design Safety AI Simulator)"):
        st.write("전력 기기 및 구조물의 재질과 무게를 기반으로 지진 발생 시의 안전성을 시뮬레이션합니다.")
        
        sim_cols = st.columns([1, 2])
        with sim_cols[0]:
            magnitude = st.slider("예상 지진 규모 (Richter)", 4.0, 9.0, 6.5, 0.1)
            soil_type = st.selectbox("지반 조건", ["연약지반 (Soft Soil)", "보통지반 (Medium Soil)", "단단한 암반 (Hard Rock)"])
            equip_weight = st.number_input("설비 총 중량 (Ton)", value=120.5)
            
            run_seismic = st.button("내진 안전성 평가", key="btn_seismic")
            
        with sim_cols[1]:
            if run_seismic:
                with st.spinner("응력 해석 및 전도 위험성 산출 중..."):
                    time.sleep(1.5)
                    # Simple heuristic for mockup
                    base_risk = (magnitude - 4.0) * 15
                    soil_factor = 1.5 if "연약" in soil_type else (1.0 if "보통" in soil_type else 0.7)
                    risk_score = min(max(base_risk * soil_factor, 0), 100)
                    
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = risk_score,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "구조물 붕괴 위험도 (Risk Level)"},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps' : [
                                {'range': [0, 30], 'color': "lightgreen"},
                                {'range': [30, 70], 'color': "yellow"},
                                {'range': [70, 100], 'color': "red"}],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 70}
                        }))
                    fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if risk_score > 70:
                        st.error("🚨 위험: 설계 기준 미달. 내진 보강 가새(Bracing) 추가 또는 마이크로파일 기초 보강이 필요합니다.")
                    else:
                        st.success("✅ 안전: 현재 시방서 기준으로 해당 지진 규모를 버틸 수 있도록 설계되었습니다.")
        
    with st.expander("🏢 스마트 변전소 3D BIM 모델링 (Smart Substation 3D BIM Modeling)"):
        st.write("2D CAD 도면 및 설계 파라미터를 기반으로 유지보수에 활용 가능한 3D BIM 객체를 자동 생성합니다.")
        
        if st.button("🏗️ 2D 레이아웃을 3D BIM으로 변환", key="btn_bim", type="primary"):
            with st.spinner("3D 객체 매핑 및 렌더링 중..."):
                time.sleep(2)
                
                # Mock 3D Substation data
                np.random.seed(42)
                n_equip = 15
                x = np.random.uniform(0, 50, n_equip)
                y = np.random.uniform(0, 50, n_equip)
                z = np.zeros(n_equip)
                
                equip_types = ['M.Tr (주변압기)', 'GIS (가스절연개폐장치)', 'SWG (배전반)', 'Control Panel']
                labels = [equip_types[i % 4] for i in range(n_equip)]
                
                fig3d = go.Figure(data=[go.Scatter3d(
                    x=x, y=y, z=z,
                    mode='markers',
                    marker=dict(
                        size=15,
                        color=np.random.randn(n_equip),
                        colorscale='Viridis',
                        opacity=0.8,
                        symbol='cube'
                    ),
                    text=labels,
                    hoverinfo='text'
                )])
                
                fig3d.update_layout(
                    margin=dict(l=0, r=0, b=0, t=0),
                    scene=dict(
                        xaxis_title='X (m)',
                        yaxis_title='Y (m)',
                        zaxis_title='Height (m)'
                    ),
                    height=400
                )
                
                st.plotly_chart(fig3d, use_container_width=True)
                st.info("💡 각 큐브에 마우스를 올리면 설비 식별 정보 확인 및 유지보수 이력(Digital Twin) 조회가 가능합니다.")
        
    with st.expander("🔥 전력기기 열화상 및 수명 예측 모델링 (Thermal & Lifespan Prediction)"):
        st.write("설비 부하량과 주변 환경 데이터를 결합하여 열화 지점(Hot-spot)을 예측하고 교체 주기를 제안합니다.")
        
        col_therm1, col_therm2 = st.columns([1, 2])
        with col_therm1:
            equip_select = st.selectbox("예측 대상 기기", ["#1 메인 변압기 (154kV)", "#2 변압기 (154kV)", "25.8kV GIS BUS"])
            env_temp = st.slider("여름철 최고 외기온도 (℃)", 30, 45, 38)
            load_factor = st.slider("예상 평균 부하율 (%)", 50, 110, 85)
            run_thermal = st.button("🔥 이상 발열 플로우 시뮬레이션", key="btn_thermal")
            
        with col_therm2:
            if run_thermal:
                with st.spinner("LSTM 시계열 모델 기반 수명 예측 중..."):
                    time.sleep(1.5)
                    
                    months = np.arange(1, 25) # 24개월 예측
                    base_temp = 60 + (env_temp - 30)*0.5 + (load_factor - 50)*0.3
                    
                    # Add non-linear degradation and noise
                    predicted_temp = base_temp + np.exp(months/10) + np.random.normal(0, 2, 24)
                    
                    fig_line = go.Figure()
                    fig_line.add_trace(go.Scatter(x=months, y=predicted_temp, mode='lines+markers', name='예상 권선 온도', line=dict(color='firebrick', width=2)))
                    fig_line.add_hline(y=95, line_dash="dash", line_color="orange", annotation_text="경고 임계치 (95℃)")
                    fig_line.add_hline(y=110, line_dash="solid", line_color="red", annotation_text="위험 폭주선 (110℃)")
                    
                    fig_line.update_layout(
                        title=f"{equip_select} 향후 24개월 최고 발열량 예측 곡선",
                        xaxis_title="경과 월 (Months)",
                        yaxis_title="최고 온도 (℃)",
                        height=350,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    
                    st.plotly_chart(fig_line, use_container_width=True)
                    
                    danger_month = np.where(predicted_temp > 95)[0]
                    if len(danger_month) > 0:
                        st.warning(f"⚠️ 예측 결과: 약 **{danger_month[0]+1}개월 후**부터 경고 온도(95℃)를 초과할 확률이 85% 이상입니다. 냉각팬 증설 또는 사전 점검 요망.")
                    else:
                        st.success("✅ 예측 결과: 향후 2년 내에 임계 온도를 초과할 위험성이 낮습니다. (정상 수명 주기 유지 예상)")
