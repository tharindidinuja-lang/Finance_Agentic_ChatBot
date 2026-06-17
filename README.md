# 🏦 Finance Agentic Chatbot

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-green.svg)](https://langchain-ai.github.io/langgraph/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange.svg)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready intelligent banking assistant built with **LangGraph** that demonstrates multi-step reasoning, tool calling, risk assessment, and human-in-the-loop approval workflows.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Deliverables](#deliverables)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Demo](#demo)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## 🎯 Overview

This Finance Agentic Chatbot is built as part of the **AI ML Engineer Program** at CodeZila Career Accelerator. It demonstrates a complete LangGraph implementation for a banking assistant capable of:

- Understanding natural language banking requests
- Planning multi-step transactions
- Executing financial operations
- Assessing risk in real-time
- Routing high-risk transactions for human review
- Maintaining conversation memory across sessions

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **🤖 Intent Classification** | Identifies user intent (balance, transfer, stock, fraud) |
| **📋 Multi-step Planning** | Breaks complex requests into executable steps |
| **🔧 Tool Integration** | 9 financial tools (balance, transfer, stock, fraud detection) |
| **✅ Validation & Retry** | Validates results with exponential backoff retry |
| **⚠️ Risk Assessment** | Real-time risk scoring (0-100) with multiple factors |
| **👥 Human-in-the-Loop** | High-risk transactions require human approval |
| **💾 Persistent Memory** | Conversation and transaction history |
| **📊 Compliance Logging** | Complete audit trail for all actions |

### Risk Detection Factors

- Transaction amount anomalies
- New recipient detection  
- Transaction velocity (too many in short time)
- Off-hours transactions
- Crypto/offshore recipient detection
- Structuring patterns (just below limits)

## 🏗️ Architecture

### LangGraph Workflow
**Flow Path:**

**Conditional Branches:**

| From Node | Condition | Next Node |
|-----------|-----------|-----------|
| Classifier | Has intent | Planner |
| Classifier | No intent | Response Generation |
| Tool Execution | Success | Validation |
| Tool Execution | Failure | Retry |
| Validation | Pass | Risk Check |
| Validation | Fail | Retry |
| Risk Check | High Risk (>70) | Human Review |
| Risk Check | Low Risk (<70) | Response Generation |
| Human Review | Approved | Tool Execution |
| Human Review | Denied | Response Generation |


### Node Descriptions

| Node | Responsibility | Input | Output |
|------|---------------|-------|--------|
| **Classifier** | Detect user intent | User message | intent, entities |
| **Planner** | Create execution plan | intent, entities | current_plan |
| **Tool Decision** | Select appropriate tool | current_plan, step | tool_calls |
| **Tool Execution** | Execute tool | tool_calls | tool_results |
| **Validation** | Validate results | tool_results | validation_status |
| **Retry** | Handle failures | validation_status, retry_count | retry_action |
| **Risk Check** | Assess transaction risk | amount, recipient | risk_score, flags |
| **Human Review** | Get human approval | risk_score, transaction | human_approved |
| **Response** | Generate user response | all results | final_response |


## 📦 Deliverables

This project fulfills all 13 required deliverables:

| # | Deliverable | Status | Location |
|---|-------------|--------|----------|
| 1 | Workflow Diagram | ✅ | `demo/workflow_diagram.txt` |
| 2 | LangGraph Implementation | ✅ | `workflows/finance_graph.py` |
| 3 | State Definition | ✅ | `state/finance_state.py` |
| 4 | Classifier Node | ✅ | `nodes/classifier_node.py` |
| 5 | Planner Node | ✅ | `nodes/planner_node.py` |
| 6 | Tool Decision Node | ✅ | `nodes/tool_decision_node.py` |
| 7 | Tool Execution Node | ✅ | `nodes/tool_execution_node.py` |
| 8 | Response Generation Node | ✅ | `nodes/response_generation_node.py` |
| 9 | Validation Node | ✅ | `nodes/validation_node.py` |
| 10 | Retry Logic | ✅ | `nodes/retry_node.py` |
| 11 | Risk Check Node | ✅ | `nodes/risk_check_node.py` |
| 12 | Human Review Routing | ✅ | `nodes/human_review_node.py` |
| 13 | Demo Inputs & Outputs | ✅ | `demo/demo_inputs.txt`, `demo/demo_outputs.json` |

---

## 🔧 Prerequisites

### Required

- **Python 3.10 or higher**
- **OpenAI API Key** - [Get one here](https://platform.openai.com/api-keys)
- **Internet connection** - For API calls

### Optional

- **Tavily API Key** - For web search (stock prices, news)

---

# 🏦 Finance Agentic Chatbot

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-green.svg)](https://langchain-ai.github.io/langgraph/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange.svg)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/tharindidinuja-lang/Finance_Agentic_ChatBot)
[![GitHub Stars](https://img.shields.io/github/stars/tharindidinuja-lang/Finance_Agentic_ChatBot?style=social)](https://github.com/tharindidinuja-lang/Finance_Agentic_ChatBot)

**View on GitHub:** [tharindidinuja-lang/Finance_Agentic_ChatBot](https://github.com/tharindidinuja-lang/Finance_Agentic_ChatBot)

A production-ready intelligent banking assistant built with **LangGraph** that demonstrates multi-step reasoning, tool calling, risk assessment, and human-in-the-loop approval workflows.

---
