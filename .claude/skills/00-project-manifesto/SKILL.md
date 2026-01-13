---
name: Project RAG SharePoint Manifesto
description: The "North Star" for the Enterprise Agentic RAG project. Use this to maintain context on the architectural shift from Passive to Agentic RAG.
---

# 🚀 Mission: Enterprise Agentic RAG

## 🎯 The Shift
We are moving beyond "Passive RAG" (linear retrieval) to **Agentic RAG**. 
- **Reasoning Plane:** The LLM acts as a reasoning engine, planning its own search queries.
- **Knowledge Plane:** Microsoft Foundry IQ (Azure AI Search) handles semantic ingestion from SharePoint.

## 🛠️ The Architecture
1. **SharePoint Online:** The Unstructured Data Plane.
2. **Azure AI Search:** The Semantic Indexing Plane (Foundry IQ).
3. **Azure AI Agent Service:** The Reasoning Plane (GPT-4 + Tools).

## 🚦 Claude's Operational Protocol
Whenever a new session starts:
1. Identify the current "Phase" of the project (Identity, Infra, Ingestion, Orchestration, or Embedding).
2. Cross-reference the specific specialized skill for that phase.
3. Prioritize **Semantic Ranking**, **Vector Embeddings**, and **Security Trimming** in all code generated.

## 📋 Project Phases
1. **Phase 1: Identity & Security** → Skill 01
2. **Phase 2: Infrastructure** → Skill 02
3. **Phase 3: Data Ingestion** → Skill 03
4. **Phase 4: Agent Orchestration** → Skill 04
5. **Phase 5: Embedding Configuration** → Skill 05 ⭐

## 🎯 Current State
✅ All 5 phases implemented
✅ Vector embeddings configured
✅ Hybrid search enabled (Keyword + Vector + Semantic)