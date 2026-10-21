"""Enterprise Hybrid RAG Retriever.

Combines BM25 token matching with Dense Semantic Similarity and Reciprocal Rank Fusion (RRF)
to achieve zero-shot and few-shot schema linking, metric identification, and SOP retrieval.
"""

from collections import Counter
import math
import re
from typing import Any, Dict, List, Set, Tuple

from cortex.config import config
from cortex.rag.metadata_catalog import (
    ENTERPRISE_METRICS,
    ENTERPRISE_TABLES,
    MetricDefinition,
    TableMetadata,
)
from cortex.rag.unstructured_kb import KNOWLEDGE_DOCUMENTS, KnowledgeDocument


def tokenize(text: str) -> List[str]:
    """Basic alphanumeric lowercased tokenizer with stopword filtering."""
    stopwords = {"a", "an", "the", "in", "on", "at", "for", "to", "of", "and", "or", "is", "are", "what", "which", "how", "show", "get", "me"}
    tokens = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    return [t for t in tokens if t not in stopwords and len(t) > 1]


class BM25Index:
    """Lightweight in-memory BM25 ranker for enterprise schema elements."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lengths: List[int] = []
        self.doc_freqs: Dict[str, int] = Counter()
        self.doc_tokens: List[List[str]] = []
        self.items: List[Any] = []

    def fit(self, items: List[Any], text_extractors: List[str]) -> None:
        self.items = items
        self.corpus_size = len(items)
        self.doc_tokens = []
        self.doc_lengths = []
        self.doc_freqs = Counter()

        for item in items:
            text = " ".join([getattr(item, attr, "") for attr in text_extractors])
            tokens = tokenize(text)
            self.doc_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freqs[t] += 1

        self.avg_doc_len = sum(self.doc_lengths) / max(1, self.corpus_size)

    def score(self, query_tokens: List[str]) -> List[Tuple[float, int]]:
        scores = []
        for idx in range(self.corpus_size):
            score = 0.0
            doc_len = self.doc_lengths[idx]
            tokens_in_doc = Counter(self.doc_tokens[idx])
            
            for q_term in query_tokens:
                if q_term not in self.doc_freqs:
                    continue
                df = self.doc_freqs[q_term]
                idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)
                tf = tokens_in_doc[q_term]
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len)))
                score += idf * ((tf * (self.k1 + 1.0)) / max(0.001, denom))
                
            scores.append((score, idx))
        return sorted(scores, key=lambda x: x[0], reverse=True)


class DenseSimilarityIndex:
    """Dense cosine similarity index using sub-word n-gram character and token embeddings."""

    def __init__(self):
        self.items: List[Any] = []
        self.vector_cache: List[Counter] = []

    def fit(self, items: List[Any], text_extractors: List[str]) -> None:
        self.items = items
        self.vector_cache = []
        for item in items:
            text = " ".join([getattr(item, attr, "") for attr in text_extractors])
            vec = self._vectorize(text)
            self.vector_cache.append(vec)

    def _vectorize(self, text: str) -> Counter:
        tokens = tokenize(text)
        vec: Counter = Counter(tokens)
        # Add character tri-grams for typo and inflection tolerance
        for t in tokens:
            if len(t) >= 4:
                for i in range(len(t) - 2):
                    vec[f"tri_{t[i:i+3]}"] += 1
        return vec

    def score(self, query: str) -> List[Tuple[float, int]]:
        q_vec = self._vectorize(query)
        q_norm = math.sqrt(sum(v * v for v in q_vec.values()))
        if q_norm == 0:
            return [(0.0, i) for i in range(len(self.items))]

        scores = []
        for idx, doc_vec in enumerate(self.vector_cache):
            d_norm = math.sqrt(sum(v * v for v in doc_vec.values()))
            if d_norm == 0:
                scores.append((0.0, idx))
                continue
            dot = sum(q_vec[k] * doc_vec[k] for k in q_vec if k in doc_vec)
            sim = dot / (q_norm * d_norm)
            scores.append((sim, idx))
        return sorted(scores, key=lambda x: x[0], reverse=True)


class HybridRetriever:
    """Enterprise RAG Retriever using Reciprocal Rank Fusion (RRF)."""

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self._init_indexes()

    def _init_indexes(self) -> None:
        # 1. Tables Index
        self.table_bm25 = BM25Index()
        self.table_dense = DenseSimilarityIndex()
        # Create searchable text representation of tables
        for t in ENTERPRISE_TABLES:
            col_text = " ".join([f"{c.name} {c.description}" for c in t.columns])
            setattr(t, "_searchable", f"{t.table_name} {t.domain} {t.description} {col_text}")
        self.table_bm25.fit(ENTERPRISE_TABLES, ["_searchable"])
        self.table_dense.fit(ENTERPRISE_TABLES, ["_searchable"])

        # 2. Metrics Index
        self.metrics_bm25 = BM25Index()
        self.metrics_dense = DenseSimilarityIndex()
        for m in ENTERPRISE_METRICS:
            setattr(m, "_searchable", f"{m.metric_name} {m.domain} {m.description} {m.formula}")
        self.metrics_bm25.fit(ENTERPRISE_METRICS, ["_searchable"])
        self.metrics_dense.fit(ENTERPRISE_METRICS, ["_searchable"])

        # 3. Documents Index
        self.docs_bm25 = BM25Index()
        self.docs_dense = DenseSimilarityIndex()
        self.docs_bm25.fit(KNOWLEDGE_DOCUMENTS, ["title", "content", "domain"])
        self.docs_dense.fit(KNOWLEDGE_DOCUMENTS, ["title", "content", "domain"])

    def _reciprocal_rank_fusion(self, ranked_list1: List[Tuple[float, int]], ranked_list2: List[Tuple[float, int]]) -> List[Tuple[float, int]]:
        """Calculates RRF score: score(d) = 1/(k + r1) + 1/(k + r2)."""
        rrf_scores: Dict[int, float] = Counter()
        for rank, (_, item_idx) in enumerate(ranked_list1):
            rrf_scores[item_idx] += 1.0 / (self.rrf_k + rank + 1)
        for rank, (_, item_idx) in enumerate(ranked_list2):
            rrf_scores[item_idx] += 1.0 / (self.rrf_k + rank + 1)
            
        return sorted([(score, idx) for idx, score in rrf_scores.items()], key=lambda x: x[0], reverse=True)

    def retrieve_schemas(self, query: str, top_k: int = 3) -> List[TableMetadata]:
        """Performs hybrid retrieval to link relevant enterprise tables for a query."""
        tokens = tokenize(query)
        bm25_ranks = self.table_bm25.score(tokens)
        dense_ranks = self.table_dense.score(query)
        fused = self._reciprocal_rank_fusion(bm25_ranks, dense_ranks)
        return [ENTERPRISE_TABLES[idx] for _, idx in fused[:top_k]]

    def retrieve_metrics(self, query: str, top_k: int = 2) -> List[MetricDefinition]:
        """Retrieves relevant semantic business metrics for calculation."""
        tokens = tokenize(query)
        bm25_ranks = self.metrics_bm25.score(tokens)
        dense_ranks = self.metrics_dense.score(query)
        fused = self._reciprocal_rank_fusion(bm25_ranks, dense_ranks)
        return [ENTERPRISE_METRICS[idx] for _, idx in fused[:top_k] if _ > 0.015]

    def retrieve_documents(self, query: str, top_k: int = 2) -> List[KnowledgeDocument]:
        """Retrieves operational SOPs and domain guidelines."""
        tokens = tokenize(query)
        bm25_ranks = self.docs_bm25.score(tokens)
        dense_ranks = self.docs_dense.score(query)
        fused = self._reciprocal_rank_fusion(bm25_ranks, dense_ranks)
        return [KNOWLEDGE_DOCUMENTS[idx] for _, idx in fused[:top_k]]

    def get_prompt_context(self, query: str) -> Dict[str, Any]:
        """Packages structured schemas, metrics, and SOPs into an agent prompt context dictionary."""
        tables = self.retrieve_schemas(query, top_k=config.top_k_schemas)
        metrics = self.retrieve_metrics(query, top_k=2)
        docs = self.retrieve_documents(query, top_k=config.top_k_docs)

        schema_ddl_list = []
        for t in tables:
            cols = [f"  {c.name} {c.data_type} -- {c.description}" for c in t.columns]
            ddl = f"TABLE {t.table_name} (\n" + ",\n".join(cols) + f"\n); -- Domain: {t.domain} | {t.description}"
            schema_ddl_list.append(ddl)

        return {
            "tables": tables,
            "metrics": metrics,
            "documents": docs,
            "schema_ddl_string": "\n\n".join(schema_ddl_list),
            "metric_definitions_string": "\n".join([f"- {m.metric_name}: {m.formula} ({m.description})" for m in metrics]),
            "sop_string": "\n\n".join([f"[{d.doc_id}] {d.title}:\n{d.content}" for d in docs]),
        }


# Singleton retriever
hybrid_retriever = HybridRetriever()
