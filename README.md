# RAG Customer Support Assistant


###NAME: TANISHKA PRASAD JADHAV
-ORG: INNOMATICS RESEARCH LABS
-INTERN ID: IN226010302
## Overview

This project now supports two workflows in one app:

- Customer support mode with customer records, policy retrieval, routing, and human escalation
- PDF assistant mode with uploaded-document processing, embedding-based retrieval, and grounded answers

## Features

- PDF knowledge base processing
- Embedding-based retrieval
- Contextual question answering
- Graph-based workflow with LangGraph
- Intent-based routing
- Human-in-the-loop escalation
- Customer-aware support responses
- Conversation history reset

## Flow

- Customer mode: customer profile -> policy retrieval -> graph routing -> reply or escalate
- PDF mode: upload PDF -> chunk document -> embed chunks -> retrieve relevant context -> answer or escalate

## Tech Stack

- Python
- Streamlit
- Sentence Transformers
- LangGraph
- Groq API
- PyPDF

## Run

1. Install requirements
2. Set `GROQ_API_KEY`
3. Start the Streamlit app

## Notes

- The embedding model uses `all-MiniLM-L6-v2`
- The repository includes sample customer data and support policies
- Uploaded PDFs are processed in memory and indexed for retrieval

## Future Improvements

- Persist customer conversations
- Add authentication and role-based access
- Connect HITL escalation to a ticketing tool
- Support multiple PDFs and persistent vector storage


## VIDEO EXPLAINATION
https://drive.google.com/file/d/1pPX9tvaZJ06_yzcIHs8zrzn7l_wWf8lG/view?usp=sharing
