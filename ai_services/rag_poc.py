import os
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def main():
    print("🚀 [Step 1] Loading documents from 'data_real' directory...")
    # Load PDFs from data_real directory
    pdf_loader = DirectoryLoader('./data_real', glob="**/*.pdf", loader_cls=PyPDFLoader)
    docs = pdf_loader.load()
    
    print(f"Loaded {len(docs)} document pages.")

    print("✂️  [Step 2] Chunking document...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    print("🧠 [Step 3] Initializing Embedding Model (huggingface/all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("🗄️  [Step 4] Building FAISS Vector Index...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    print("💾  [Step 5] Saving FAISS Vector Index to disk...")
    vectorstore.save_local("faiss_index")
    
    print("\n✅ Verification Complete: RAG Indexing successful and saved to 'faiss_index'!")
    print("-" * 50)
    
    queries = [
        "국가철도공단의 설립 목적은 무엇인가요?",
        "전기안전관리자의 직무는 어떻게 되나요?",
        "철도안전법에 따른 안전관리체계 승인 대상은 누구인가요?"
    ]

    for q in queries:
        print(f"\n❓ 질의 (Query): {q}")
        results = vectorstore.similarity_search(q, k=1)
        print(f"💡 검색된 출처: {results[0].metadata.get('source', '알 수 없음')} (페이지: {results[0].metadata.get('page', '알 수 없음')})")
        print(f"💡 AI 유사도 검색 결과:\n{results[0].page_content.strip()}")
        print("-" * 50)

if __name__ == "__main__":
    main()
