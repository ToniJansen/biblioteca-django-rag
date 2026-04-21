"""Interface publica do chat conversacional sobre o acervo.

Pipeline RAG: a pergunta do usuario e vetorizada, os top-k livros do acervo
mais similares sao recuperados via embeddings (HuggingFace MiniLM), o contexto
e enviado ao LLM hospedado na Groq (Llama 3.3 70B) e a resposta sintetizada
e devolvida para a interface.

A implementacao real esta em `rag.py`. Este modulo mantem o contrato estavel
(dataclass `RespostaChat` + funcao `responder_pergunta`) para que a camada
de views nao precise conhecer os detalhes do pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RespostaChat:
    texto: str
    obras_citadas: List[int] = field(default_factory=list)  # ids de livros
    confianca: float = 0.0                                   # 0.0 - 1.0


def responder_pergunta(
    pergunta: str,
    historico: Optional[List[str]] = None,
    leitor_id: Optional[int] = None,
) -> RespostaChat:
    """Entry-point do chat. Delega para o pipeline RAG."""
    # import local para evitar carregar groq/sentence-transformers em imports altos
    from .rag import responder
    return responder(pergunta)
