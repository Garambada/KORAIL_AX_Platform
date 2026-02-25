import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def main():
    print("🚀 [Step 1] Loading '실무보감_전철전력_요약.md'...")
    loader = TextLoader("실무보감_전철전력_요약.md", encoding="utf-8")
    docs = loader.load()

    print("✂️  [Step 2] Chunking document...")
    splitter = MarkdownTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    print("🧠 [Step 3] Initializing Embedding Model (huggingface/all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("🗄️  [Step 4] Building FAISS Vector Index...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    print("\n✅ Verification Complete: RAG Indexing successful!")
    print("-" * 50)
    
    queries = [
        "품질관리계획서는 계약 후 며칠 이내에 제출해야 하나요?",
        "전차선로 고속선 장력 기준은 무엇인가요?",
        "실무보감이 가진 한계점은 어떤 것들이 있나요?"
    ]

    for q in queries:
        print(f"\n❓ 질의 (Query): {q}")
        results = vectorstore.similarity_search(q, k=1)
        print(f"💡 AI 유사도 검색 결과:\n{results[0].page_content.strip()}")
        print("-" * 50)

if __name__ == "__main__":
    main()
