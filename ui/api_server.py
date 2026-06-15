# ui/api_server.py
"""FastAPI REST API for Finance Agentic Chatbot"""

import sys
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException, Depends, status
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.finance_agent import create_finance_agent
from config.settings import get_settings
from data import DataManager

# ============================================================================
# Pydantic Models
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message", min_length=1, max_length=5000)
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="Agent response")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session ID")
    timestamp: str = Field(..., description="Response timestamp")
    risk_score: int = Field(0, description="Risk score (0-100)")
    needs_human_review: bool = Field(False, description="Whether human review is required")
    transaction_id: Optional[str] = Field(None, description="Transaction ID if applicable")


class TransferRequest(BaseModel):
    """Transfer request model"""
    user_id: str = Field(..., description="User identifier")
    amount: float = Field(..., description="Transfer amount", gt=0)
    from_account: str = Field("checking", description="Source account")
    to_account: str = Field(..., description="Destination account")
    description: Optional[str] = Field(None, description="Transfer description")


class TransferResponse(BaseModel):
    """Transfer response model"""
    success: bool
    transaction_id: Optional[str] = None
    message: str
    risk_score: int
    requires_review: bool


class BalanceRequest(BaseModel):
    """Balance request model"""
    user_id: str = Field(..., description="User identifier")
    account_type: str = Field("checking", description="Account type (checking/savings)")


class BalanceResponse(BaseModel):
    """Balance response model"""
    user_id: str
    account_type: str
    balance: float
    currency: str = "USD"
    timestamp: str


class TransactionHistoryRequest(BaseModel):
    """Transaction history request"""
    user_id: str = Field(..., description="User identifier")
    limit: int = Field(10, description="Number of transactions to return", ge=1, le=100)
    days: int = Field(30, description="Days to look back", ge=1, le=365)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str
    environment: str


# ============================================================================
# FastAPI Application
# ============================================================================

# Global agent instance
agent = None
data_manager = None
settings = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global agent, data_manager, settings
    
    # Startup
    print("Starting Finance Agent API Server...")
    settings = get_settings()
    agent = create_finance_agent()
    data_manager = DataManager()
    print(f"Server started on environment: {settings.app_env}")
    
    yield
    
    # Shutdown
    print("Shutting down Finance Agent API Server...")


app = FastAPI(
    title="Finance Agentic Chatbot API",
    description="REST API for intelligent banking assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Finance Agentic Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        environment=settings.app_env
    )
