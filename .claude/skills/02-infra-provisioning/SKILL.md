---
name: Azure Infrastructure Provisioner
description: Handles the setup of the Knowledge and Reasoning Planes.
---

# 🏗️ Infrastructure Setup (Phase 2)

## 📋 Resource Requirements
Claude, verify the user has the following in the SAME region:
1. **Azure AI Search:** Must be **Basic** or higher (Free tier will fail for Foundry IQ).
2. **Azure AI Foundry Hub & Project:** The container for the agent.
3. **Azure OpenAI:** Specifically for `text-embedding-ada-002` or `text-embedding-3-small`.

## ⚙️ Feature Activation
1. **Enable Semantic Ranker:** Direct user to Azure AI Search > Semantic Ranker > Enable (Free/Standard).
2. **Project Connection:** Guide user to AI Foundry > Management Center > Connected Resources > Add Azure AI Search.

## 💻 CLI Helper
Provide this command to bridge the planes:
`az ml connection create --file search_connection.yml --resource-group [RG] --workspace-name [FoundryProject]`