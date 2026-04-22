import io
import warnings
from functools import lru_cache

import numpy as np
from groq import Groq
from pypdf import PdfReader

import backend.config as support_config


warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
)

from langchain_core.documents import Document


CUSTOMER_RECORDS = getattr(support_config, "CUSTOMER_RECORDS", {})
EMBEDDING_MODEL_NAME = getattr(
    support_config,
    "EMBEDDING_MODEL_NAME",
    "all-MiniLM-L6-v2",
)
GROQ_API_KEY = getattr(support_config, "GROQ_API_KEY", None)
MODEL_NAME = getattr(support_config, "MODEL_NAME", "llama-3.1-8b-instant")
SUPPORT_KNOWLEDGE_BASE = getattr(support_config, "SUPPORT_KNOWLEDGE_BASE", [])


def chunk_text(text, chunk_size=500, overlap=80):
    chunks = []
    start = 0
    cleaned_text = " ".join(text.split())

    while start < len(cleaned_text):
        end = start + chunk_size
        chunks.append(cleaned_text[start:end])
        start += chunk_size - overlap

    return chunks


@lru_cache(maxsize=1)
def get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
    except Exception as exc:
        raise RuntimeError(
            f"Embedding model '{EMBEDDING_MODEL_NAME}' could not be loaded locally."
        ) from exc


def embed_texts(texts):
    model = get_embedding_model()
    return np.asarray(
        model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
    )


class EmbeddingRetriever:
    def __init__(self, documents, k=3):
        self.documents = documents
        self.k = k
        self.document_embeddings = (
            embed_texts([document.page_content for document in documents])
            if documents
            else np.empty((0, 0))
        )

    def invoke(self, query):
        if not self.documents:
            return []

        query_embedding = embed_texts([query])[0]
        scores = self.document_embeddings @ query_embedding
        ranked_indices = np.argsort(scores)[::-1][: self.k]
        return [self.documents[index] for index in ranked_indices]


def build_support_documents():
    documents = []

    for article in SUPPORT_KNOWLEDGE_BASE:
        article_text = (
            f"Article: {article['title']}\n"
            f"Category: {article['category']}\n"
            f"Content: {article['content']}"
        )

        for chunk_index, chunk in enumerate(chunk_text(article_text)):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "title": article["title"],
                        "category": article["category"],
                        "chunk_index": chunk_index,
                        "source_type": "support_kb",
                    },
                )
            )

    return documents


def build_support_retriever():
    return EmbeddingRetriever(build_support_documents())


def load_pdf_text(file_bytes):
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages.append(page_text)

    return "\n".join(pages), len(reader.pages)


def build_pdf_documents(file_bytes, file_name):
    pdf_text, page_count = load_pdf_text(file_bytes)
    if not pdf_text.strip():
        raise ValueError("The uploaded PDF does not contain extractable text.")

    documents = []
    chunks = chunk_text(pdf_text)

    for chunk_index, chunk in enumerate(chunks):
        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    "title": file_name,
                    "category": "PDF",
                    "chunk_index": chunk_index,
                    "source_type": "pdf",
                },
            )
        )

    return documents, {
        "file_name": file_name,
        "page_count": page_count,
        "chunk_count": len(chunks),
    }


def build_pdf_retriever(file_bytes, file_name):
    documents, metadata = build_pdf_documents(file_bytes, file_name)
    return EmbeddingRetriever(documents), metadata


def get_customer_record(customer_id):
    return CUSTOMER_RECORDS.get(customer_id)


def get_order_record(customer_record, order_id):
    if not customer_record or not order_id:
        return None

    for order in customer_record.get("orders", []):
        if order["order_id"] == order_id:
            return order

    return None


def format_customer_context(customer_record, order_id=None):
    if not customer_record:
        return "Customer record not found."

    selected_order = get_order_record(customer_record, order_id)
    orders = [selected_order] if selected_order else customer_record.get("orders", [])

    order_lines = []
    for order in orders:
        order_lines.append(
            (
                f"- {order['order_id']}: {order['item']} | Status: {order['status']} | "
                f"Placed: {order['placed_on']} | {order['delivery_date']} | Amount: {order['amount']}"
            )
        )

    order_summary = "\n".join(order_lines) if order_lines else "- No orders available."

    return (
        f"Customer ID: {customer_record['customer_id']}\n"
        f"Name: {customer_record['name']}\n"
        f"Email: {customer_record['email']}\n"
        f"Plan: {customer_record['plan']}\n"
        f"Account Status: {customer_record['account_status']}\n"
        f"Region: {customer_record['region']}\n"
        f"Preferred Channel: {customer_record['preferred_channel']}\n"
        f"Renewal Date: {customer_record['renewal_date']}\n"
        f"Last Ticket: {customer_record['last_ticket']}\n"
        f"Notes: {customer_record['notes']}\n"
        f"Orders:\n{order_summary}"
    )


client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def generate_answer(
    context,
    question,
    source_type,
    customer_context=None,
    issue_type=None,
    order_id=None,
    file_name=None,
):
    if client is None:
        return (
            "The knowledge base is ready, but GROQ_API_KEY is not configured. "
            "Set the API key to generate answers."
        )

    if source_type == "customer":
        order_scope = order_id if order_id else "Account overview"
        prompt = f"""
You are a professional customer support assistant.

Use only the verified support knowledge and verified customer record below.
Do not invent refunds, credits, shipping promises, or account actions.
If the request needs manual review or the information is incomplete, clearly say that the case should be escalated to human support.
Write a concise, warm answer that can be shown directly to the customer.

Issue Type:
{issue_type}

Order Scope:
{order_scope}

Verified Customer Record:
{customer_context}

Verified Support Knowledge:
{context}

Customer Question:
{question}

Answer:
"""
    else:
        prompt = f"""
You are a document question-answering assistant.

Answer only from the retrieved excerpts of the uploaded PDF.
If the excerpts do not contain enough information, say that the uploaded document does not contain enough information to answer the question.
Keep the answer concise and professional.

Document:
{file_name or "Uploaded PDF"}

Retrieved Excerpts:
{context}

Question:
{question}

Answer:
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=450,
        )
    except Exception:
        return (
            "The retrieval flow is working, but the Groq service could not be reached. "
            "Check network access and GROQ_API_KEY, or route this request to a human agent."
        )

    return response.choices[0].message.content
