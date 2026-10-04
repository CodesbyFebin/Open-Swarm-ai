#!/usr/bin/env python3
"""
Solana Intelligence Platform - REST API Service
Exposes agent capabilities through FastAPI endpoints
"""

import sys
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import uuid
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from openswarm.agents.solana_audit_agent import SolanaAuditAgent
from openswarm.agents.solana_defi_agent import SolanaDeFiAgent
from openswarm.agents.solana_execution_agent import SolanaExecutionAgent
from openswarm.utils.solana_utils import DefiDataFetcher, TokenInfo

# FastAPI app setup
app = FastAPI(
    title="Solana Intelligence Platform API",
    description="Multi-agent swarm for smart contract security auditing and DeFi yield optimization",
    version="1.0.0",
)

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ContractAuditRequest(BaseModel):
    contract_code: str
    contract_address: str
    mock_mode: bool = True


class ContractAuditResponse(BaseModel):
    status: str
    contract_address: str
    findings: str
    timestamp: str


class DefiAnalysisRequest(BaseModel):
    wallet_address: str
    positions: Dict[str, float]
    action: str = "analyze"  # analyze or rebalance
    use_real_data: bool = False
    mock_mode: bool = True


class DefiAnalysisResponse(BaseModel):
    status: str
    wallet_address: str
    recommendation: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    timestamp: str


class TransactionBuildRequest(BaseModel):
    action_type: str  # swap, stake, unstake, multi_swap
    params: Dict[str, Any]


class TransactionBuildResponse(BaseModel):
    status: str
    action_type: str
    transaction: Optional[Dict[str, Any]] = None
    timestamp: str


class PoolDataResponse(BaseModel):
    total_pools: int
    top_pools: list
    timestamp: str


class TokenPriceRequest(BaseModel):
    mint_addresses: list


class TokenPriceResponse(BaseModel):
    prices: Dict[str, float]
    timestamp: str


class WalletAnalysisRequest(BaseModel):
    wallet_address: str


class WalletAnalysisResponse(BaseModel):
    sol_balance: float
    tokens: Dict[str, float]
    timestamp: str


# In-memory job tracking
jobs = {}


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Solana Intelligence Platform",
        "version": "1.0.0"
    }


# Audit endpoints
@app.post("/api/v1/audit/contract", response_model=ContractAuditResponse)
async def audit_contract(request: ContractAuditRequest):
    """Audit a smart contract for vulnerabilities"""
    try:
        agent = SolanaAuditAgent(mock_mode=request.mock_mode)
        result = await agent.execute("Audit contract", {
            "contract_code": request.contract_code,
            "contract_address": request.contract_address,
        })

        return ContractAuditResponse(
            status=result.get("status", "unknown"),
            contract_address=result.get("contract_address", ""),
            findings=result.get("findings", ""),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DeFi endpoints
@app.post("/api/v1/defi/analyze", response_model=DefiAnalysisResponse)
async def analyze_defi_portfolio(request: DefiAnalysisRequest):
    """Analyze DeFi portfolio and recommend yield optimization"""
    try:
        agent = SolanaDeFiAgent(
            mock_mode=request.mock_mode,
            use_real_data=request.use_real_data
        )

        result = await agent.execute("Analyze positions", {
            "wallet_address": request.wallet_address,
            "positions": request.positions,
            "action": request.action,
        })

        return DefiAnalysisResponse(
            status=result.get("status", "unknown"),
            wallet_address=result.get("wallet_address", ""),
            recommendation=result.get("recommendation"),
            plan=result.get("plan"),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Execution endpoints
@app.post("/api/v1/execution/build-transaction", response_model=TransactionBuildResponse)
async def build_transaction(request: TransactionBuildRequest):
    """Build a transaction for execution"""
    try:
        agent = SolanaExecutionAgent()
        result = await agent.execute("Build transaction", {
            "action_type": request.action_type,
            "params": request.params,
        })

        return TransactionBuildResponse(
            status=result.get("status", "unknown"),
            action_type=request.action_type,
            transaction=result.get("transaction"),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Data endpoints
@app.get("/api/v1/data/defi-pools", response_model=PoolDataResponse)
async def get_defi_pools():
    """Get live DeFi pool data"""
    try:
        fetcher = DefiDataFetcher()
        pools_data = await fetcher.get_defillama_pools()
        await fetcher.close()

        if "error" in pools_data:
            raise HTTPException(status_code=503, detail="Failed to fetch pool data")

        pools = pools_data.get("pools", [])
        top_pools = sorted(
            pools,
            key=lambda p: float(p.get("tvlUsd", 0)),
            reverse=True
        )[:20]

        return PoolDataResponse(
            total_pools=len(pools),
            top_pools=top_pools,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/data/token-prices", response_model=TokenPriceResponse)
async def get_token_prices(request: TokenPriceRequest):
    """Get current token prices"""
    try:
        fetcher = DefiDataFetcher()
        prices = await fetcher.get_jupiter_prices(request.mint_addresses)
        await fetcher.close()

        if "error" in prices:
            return TokenPriceResponse(
                prices={},
                timestamp=datetime.utcnow().isoformat()
            )

        return TokenPriceResponse(
            prices=prices.get("prices", {}),
            timestamp=prices.get("timestamp", datetime.utcnow().isoformat())
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Composite endpoints (combining multiple agents)
@app.post("/api/v1/intelligence/full-analysis")
async def full_intelligence_analysis(
    contract_code: str,
    contract_address: str,
    wallet_address: str,
    positions: Dict[str, float],
    use_real_data: bool = False
):
    """Run full intelligence swarm (audit + DeFi + execution)"""
    try:
        # Parallel execution
        audit_task = SolanaAuditAgent(mock_mode=True).execute("Audit", {
            "contract_code": contract_code,
            "contract_address": contract_address,
        })

        defi_task = SolanaDeFiAgent(mock_mode=True, use_real_data=use_real_data).execute(
            "Analyze", {
                "wallet_address": wallet_address,
                "positions": positions,
                "action": "analyze",
            }
        )

        audit_result, defi_result = await asyncio.gather(audit_task, defi_task)

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "audit": audit_result,
            "defi": defi_result,
            "synthesis": {
                "security_status": audit_result.get("status"),
                "portfolio_status": defi_result.get("status"),
                "recommended_actions": "Review audit findings before proceeding",
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Utility endpoints
@app.get("/api/v1/utils/token-info/{mint}")
async def get_token_info(mint: str):
    """Get token information by mint address"""
    info = TokenInfo.get_token_info(mint)
    return {
        "mint": mint,
        **info,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/utils/supported-protocols")
async def get_supported_protocols():
    """Get list of supported DeFi protocols"""
    return {
        "protocols": [
            {"name": "Marinade", "symbol": "mSOL", "type": "staking", "apy_range": "4-10%"},
            {"name": "Orca", "symbol": "ORCA", "type": "dex", "apy_range": "5-20%"},
            {"name": "Raydium", "symbol": "RAY", "type": "dex", "apy_range": "10-50%"},
            {"name": "Jupiter", "symbol": "JUP", "type": "aggregator", "apy_range": "variable"},
            {"name": "Magic Eden", "symbol": "MAGIC", "type": "marketplace", "apy_range": "0-5%"},
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


# Documentation
@app.get("/api/v1/docs")
async def api_documentation():
    """API documentation and usage examples"""
    return {
        "title": "Solana Intelligence Platform API",
        "version": "1.0.0",
        "endpoints": {
            "audit": {
                "POST /api/v1/audit/contract": "Audit smart contract for vulnerabilities",
            },
            "defi": {
                "POST /api/v1/defi/analyze": "Analyze portfolio and recommend yields",
            },
            "execution": {
                "POST /api/v1/execution/build-transaction": "Build transaction for execution",
            },
            "data": {
                "GET /api/v1/data/defi-pools": "Get live DeFi pool data",
                "POST /api/v1/data/token-prices": "Get token prices",
            },
            "intelligence": {
                "POST /api/v1/intelligence/full-analysis": "Run complete swarm analysis",
            },
            "utils": {
                "GET /api/v1/utils/token-info/{mint}": "Get token metadata",
                "GET /api/v1/utils/supported-protocols": "List supported protocols",
            },
        },
        "examples": {
            "contract_audit": {
                "endpoint": "POST /api/v1/audit/contract",
                "request": {
                    "contract_code": "pub mod example { ... }",
                    "contract_address": "11111111111111111111111111111111",
                    "mock_mode": True
                }
            },
            "defi_analysis": {
                "endpoint": "POST /api/v1/defi/analyze",
                "request": {
                    "wallet_address": "So11111111...",
                    "positions": {"SOL": 100, "USDC": 50000},
                    "action": "analyze"
                }
            }
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
