# 🚆 KORAIL AX Platform (AI Services PoC)

한국철도공사(KORAIL) 전철전력처의 AI 전환(AX)을 위한 핵심 과제(공통, 설계, 시공, SCADA) PoC 구현 레포지토리입니다.

## 🚀 Module 01: 공통업무 AI (RAG 문서 어시스턴트)

이 저장소는 `Streamlit Community Cloud`를 통한 배포를 지원합니다.
'전철전력 실무보감' 문서를 기반으로 Upstage Solar Pro3 LLM API를 연동하여 질의응답(RAG) 기능을 수행합니다.

### 🌐 배포(디플로이) 방법

이 레포지토리를 사용자의 GitHub 계정에 Fork(포크) 또는 Push(푸시) 한 후 다음 단계를 따르세요:

1.  **[Streamlit Community Cloud](https://share.streamlit.io/)** 에 로그인합니다 (GitHub 계정 연동).
2.  우측 상단의 **"New app"** 버튼을 클릭합니다.
3.  **"Use existing repo"** 를 선택합니다.
4.  설정값을 아래와 같이 입력합니다:
    *   **Repository:** `사용자아이디/KORAIL_AX_Platform`
    *   **Branch:** `main`
    *   **Main file path:** `ai_services/streamlit_app.py`
5.  **"Advanced settings"** 를 클릭하여 환경 변수(Secrets)를 설정합니다. 아래 텍스트 상자에 API 키를 붙여넣으세요:
    ```toml
    UPSTAGE_API_KEY="up_mK2h7yONqSmhFo8WfFIsr35B1hy83"
    ```
6.  **"Deploy!"** 버튼을 클릭합니다. 약 1~2분 후 의존성 설치 및 FAISS 인덱싱이 끝나면 웹앱이 구동됩니다.

### 🛠 로컬 실행 방법 (Local Development)

```bash
cd ai_services
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```
