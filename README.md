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
