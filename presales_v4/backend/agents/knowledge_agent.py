"""
agents/knowledge_agent.py
--------------------------
RAG knowledge retrieval using modern LangChain LCEL (LangChain >= 1.x).
Results → state["domain_knowledge"], state["roi_knowledge"]
"""
import json

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter

from llm_factory import get_llm, get_embeddings


def _format_docs(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)


class KnowledgeAgent:
    def __init__(self, knowledge_file: str = "data/industry_knowledge.txt"):
        llm        = get_llm(temperature=0)
        embeddings = get_embeddings()

        loader = TextLoader(knowledge_file, encoding="utf-8")
        docs   = loader.load()
        chunks = RecursiveCharacterTextSplitter(
            chunk_size=600, chunk_overlap=80
        ).split_documents(docs)

        vs = Chroma.from_documents(chunks, embeddings, collection_name="mfg_knowledge")

        rag_prompt = ChatPromptTemplate.from_template(
            "You are a manufacturing domain expert. "
            "Use the context below to answer accurately and concisely.\n\n"
            "Context:\n{context}\n\nQuestion:\n{question}"
        )

        self._domain_chain = (
            {"context": vs.as_retriever(search_kwargs={"k": 5}) | _format_docs,
             "question": RunnablePassthrough()}
            | rag_prompt | llm | StrOutputParser()
        )
        self._roi_chain = (
            {"context": vs.as_retriever(search_kwargs={"k": 3}) | _format_docs,
             "question": RunnablePassthrough()}
            | rag_prompt | llm | StrOutputParser()
        )

    def run(self, state: dict) -> dict:
        req = json.dumps(state.get("requirements", {}))

        state["domain_knowledge"] = self._domain_chain.invoke(
            f"Based on these manufacturing requirements: {req}\n"
            "Provide: 1) Recommended MES modules 2) Key process steps "
            "3) Integration patterns 4) Industry best practices."
        )
        state["roi_knowledge"] = self._roi_chain.invoke(
            f"Based on these requirements: {req}\n"
            "Extract financial benchmarks, typical MES payback periods, "
            "cost-reduction potentials and efficiency gains."
        )
        return state
