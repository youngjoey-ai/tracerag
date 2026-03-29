from typing import TypedDict

from sqlalchemy.orm import Session
from app.services.retrieval import similarity_search
from app.prompts.rag_prompt import build_prompt
from app.services.llm import generate_answer

from langgraph.graph import StateGraph, END


class AskState(TypedDict):
    query: str
    top_k: int
    results: list
    answer: str


def retrieve_node(state: AskState, db: Session) -> AskState:
    results = similarity_search(query=state["query"], db=db, top_k=state["top_k"])
    return {"results": results}

def generate_node(state: AskState) -> AskState:
    prompt = build_prompt(query=state["query"], results=state["results"])
    try:
        answer = generate_answer(prompt)
    except Exception:
        answer = "抱歉，当前生成答案时出现异常，请稍后重试。"
    return {"answer": answer}

def fallback_node(state: AskState) -> AskState:
    return {"answer": "根据当前检索到的资料，无法确定答案。"}

def route_after_retrieve(state: AskState) -> str:
    if state["results"]:
        return "generate"
    return "fallback"

def build_ask_graph(db: Session):
    graph = StateGraph(AskState)
    
    graph.add_node("retrieve", lambda state: retrieve_node(state, db))
    graph.add_node("generate", generate_node)
    graph.add_node("fallback", fallback_node)

    graph.set_entry_point("retrieve")
    graph.add_conditional_edges("retrieve", route_after_retrieve)
    
    graph.add_edge("generate", END)
    graph.add_edge("fallback", END)
    
    return graph.compile()