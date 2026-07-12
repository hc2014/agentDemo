import os
import re
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import DirectoryLoader, Docx2txtLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_community.vectorstores import FAISS

# ================= 1. 配置阿里云百炼 API =================
API_KEY = os.getenv("QWEN_PLUS")
BASE_URL = "https://llm-e7m788c1nugxtk2f.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"

# ================= 2. 初始化模型与向量库 =================
model = ChatOpenAI(model="qwen-plus", api_key=API_KEY, base_url=BASE_URL, temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-v3", api_key=API_KEY, base_url=BASE_URL, check_embedding_ctx_length=False, chunk_size=10)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCX_PATH = os.path.join(CURRENT_DIR, "..", "docx")
FAISS_INDEX_PATH = os.path.join(CURRENT_DIR, "faiss_index")

def create_or_load_vectorstore():
    if os.path.exists(FAISS_INDEX_PATH):
        print("📚 检测到本地向量库，正在加载...")
        return FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    
    print("📄 正在读取 Word 文档并构建向量库...")
    loader = DirectoryLoader(DOCX_PATH, glob="**/*.docx", loader_cls=Docx2txtLoader)
    documents = loader.load()
    
    md_splits = []
    for doc in documents:
        text = doc.page_content.strip()
        if not text: continue
        text = re.sub(r'^(\d+)\.\s+(.+)$', r'## \2', text, flags=re.MULTILINE)
        text = re.sub(r'^(\d+\.\d+)\s+(.+)$', r'### \2', text, flags=re.MULTILINE)
        headers_to_split_on = [("##", "H2"), ("###", "H3")]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_splits.extend(markdown_splitter.split_text(text))
        
    clean_splits = [s for s in md_splits if s.page_content.strip()]
    print(f"🧹 结构化切片完成，共生成 {len(clean_splits)} 个文本块。")
    
    vectorstore = FAISS.from_documents(clean_splits, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)
    print("✅ 向量库构建完成并保存！")
    return vectorstore

vectorstore = create_or_load_vectorstore()
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ================= 3. 构建纯粹的 RAG 问答链 =================
# 极其严格的 Prompt，只允许大模型做阅读理解
prompt = ChatPromptTemplate.from_template("""
你是一个企业规章制度查询机器人。请严格根据以下【参考文档】回答用户的问题。
【核心规则】：
1. 只能回答用户问到的具体事项，绝对禁止科普或总结其他不相关的制度。
2. 必须原封不动地使用【参考文档】中的文字，禁止添加任何“根据文档”、“为您总结如下”等废话。
3. 如果【参考文档】中没有相关信息，只回复：“规章制度中未找到相关说明”。

【参考文档】：
{context}

【用户问题】：
{question}
""")

# ================= 4. 运行问答循环 =================
if __name__ == "__main__":
    print("\n🤖 企业规章制度问答助手已启动！(输入 'exit' 退出)")
    while True:
        user_input = input("\n🙋 你的问题: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        # 1. 提取关键词去检索（这里可以复用之前的硬控逻辑，或者直接搜）
        specific_keywords = ["婚假", "事假", "病假", "年假", "产假", "陪产假", "丧假", "调休", "办公用品", "报销", "出差"]
        matched_keywords = [kw for kw in specific_keywords if kw in user_input]
        search_query = " ".join(matched_keywords) if matched_keywords else user_input
        
        # 2. 检索文档
        relevant_docs = retriever.invoke(search_query)
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # 3. 直接调用大模型生成最终答案（没有 Agent 的中间思考环节）
        formatted_prompt = prompt.format_messages(context=context_text, question=user_input)
        response = model.invoke(formatted_prompt)
        
        print(f"\n💡 助手回答: {response.content}")