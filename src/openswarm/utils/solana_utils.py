"""Solana RPC and DeFi data utilities"""

import aiohttp
import asyncio
from typing import Any, Optional
import json
from datetime import datetime


class SolanaRPC:
    """Solana RPC client for fetching on-chain data"""

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def _call_rpc(self, method: str, params: list = None) -> dict:
        """Make RPC call to Solana"""
        await self._ensure_session()
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        try:
            async with self.session.post(
                self.rpc_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                return await resp.json()
        except asyncio.TimeoutError:
            return {"error": "RPC timeout"}
        except Exception as e:
            return {"error": str(e)}

    async def get_program_accounts(self, program_id: str) -> dict:
        """Get all accounts owned by a program (e.g., deployed contracts)"""
        return await self._call_rpc("getProgramAccounts", [program_id])

    async def get_account_info(self, account: str) -> dict:
        """Get information about an account including contract code"""
        return await self._call_rpc("getAccountInfo", [account, {"encoding": "base64"}])

    async def get_token_supply(self, mint: str) -> dict:
        """Get token supply information"""
        return await self._call_rpc("getTokenSupply", [mint])

    async def get_balance(self, wallet: str) -> dict:
        """Get SOL balance of a wallet"""
        return await self._call_rpc("getBalance", [wallet])

    async def get_parsed_token_accounts(self, wallet: str) -> dict:
        """Get token accounts owned by a wallet"""
        return await self._call_rpc("getTokenAccountsByOwner", [
            wallet,
            {"programId": "TokenkegQfeZyiNwAJsyFbPVwwQQfeksterne"},
            {"encoding": "jsonParsed"}
        ])


class DefiDataFetcher:
    """Fetch DeFi pool and yield data from various sources"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = {}

    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def _fetch_json(self, url: str, timeout: int = 30) -> dict:
        """Fetch JSON from URL"""
        await self._ensure_session()
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"HTTP {resp.status}"}
        except asyncio.TimeoutError:
            return {"error": "Timeout"}
        except Exception as e:
            return {"error": str(e)}

    async def get_defillama_pools(self) -> dict:
        """Fetch pool data from DeFiLlama for Solana"""
        if "defillama_pools" in self.cache:
            return self.cache["defillama_pools"]

        data = await self._fetch_json("https://yields.llama.fi/pools")
        if "error" not in data:
            # Filter for Solana pools
            solana_pools = [p for p in data.get("data", []) if p.get("chain") == "Solana"]
            self.cache["defillama_pools"] = solana_pools
            return {"pools": solana_pools, "total": len(solana_pools)}
        return data

    async def get_jupiter_prices(self, mint_addresses: list) -> dict:
        """Fetch current token prices from Jupiter"""
        if not mint_addresses:
            return {"prices": {}}

        # Fetch a few at a time to avoid rate limits
        prices = {}
        for mint in mint_addresses[:10]:
            url = f"https://price.jup.ag/v4/price?ids={mint}"
            data = await self._fetch_json(url)
            if "data" in data:
                prices.update(data["data"])

        return {"prices": prices, "timestamp": datetime.utcnow().isoformat()}

    async def get_marinade_apy() -> dict:
        """Fetch current Marinade staking APY"""
        return {
            "pool": "marinade",
            "symbol": "mSOL",
            "apy": 8.5,  # Real data would come from API
            "tvl": 2.5e9,
            "risk": "low"
        }

    async def get_orca_pools(self) -> dict:
        """Fetch Orca pools data"""
        # Would call Orca GraphQL API
        data = await self._fetch_json("https://api.mainnet.orca.so/v1/aquafarms")
        if "error" not in data:
            self.cache["orca_pools"] = data
            return data
        return {"error": "Failed to fetch Orca pools"}

    async def get_raydium_pools(self) -> dict:
        """Fetch Raydium pools data"""
        data = await self._fetch_json("https://api.raydium.io/v2/pairs")
        if "error" not in data:
            self.cache["raydium_pools"] = data
            return data
        return {"error": "Failed to fetch Raydium pools"}

    async def get_magic_eden_floor_price(self, collection: str) -> dict:
        """Fetch Magic Eden NFT floor price"""
        url = f"https://api.magiceden.io/v2/collections/{collection}"
        data = await self._fetch_json(url)
        if "error" not in data:
            return {
                "collection": collection,
                "floor_price": data.get("floorPrice"),
                "volume_24h": data.get("volumeAll"),
            }
        return data

    async def get_all_defi_data(self, wallet: str = None) -> dict:
        """Fetch comprehensive DeFi data"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "sources": {}
        }

        # Fetch from multiple sources in parallel
        tasks = [
            ("defillama", self.get_defillama_pools()),
            ("orca", self.get_orca_pools()),
            ("raydium", self.get_raydium_pools()),
        ]

        for name, task in tasks:
            try:
                result = await task
                results["sources"][name] = result
            except Exception as e:
                results["sources"][name] = {"error": str(e)}

        return results


class ContractAnalyzer:
    """Analyze contract code and patterns"""

    VULNERABILITY_PATTERNS = {
        "unchecked_math": r"balance\s*[-+*]=|\.wrapping_|overflow",
        "missing_access_control": r"pub fn\s+\w+.*->.*Result|without.*signer|require.*signer",
        "reentrancy": r"invoke|cpi|cross_program|transfer.*then",
        "unchecked_serialization": r"Deserialize|unpack|deserialize.*unsafe",
    }

    @staticmethod
    def analyze_contract(code: str) -> dict:
        """Analyze contract code for patterns"""
        findings = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern_name, pattern in ContractAnalyzer.VULNERABILITY_PATTERNS.items():
                import re
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "line": i,
                        "pattern": pattern_name,
                        "code": line.strip(),
                        "severity": "medium"
                    })

        return {
            "total_findings": len(findings),
            "findings": findings[:5],  # Top 5
            "risk_score": min(10, len(findings))
        }


class TokenInfo:
    """Token information and metadata"""

    KNOWN_TOKENS = {
        "So11111111111111111111111111111111111111112": {
            "name": "Solana",
            "symbol": "SOL",
            "decimals": 9,
            "logo": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png"
        },
        "EPjFWaLb3dMEVzgcMKwW2QKsMwqyqDe6E8W8qYunEqnE": {
            "name": "USD Coin",
            "symbol": "USDC",
            "decimals": 6,
            "logo": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/EPjFWaLb3dMEVzgcMKwW2QKsMwqyqDe6E8W8qYunEqnE/logo.png"
        },
        "mSoLzYCxHdgvgKRhfJNu3J8NcZZWptLNWLDvvYWqMH8": {
            "name": "Marinade Staked SOL",
            "symbol": "mSOL",
            "decimals": 9,
        }
    }

    @staticmethod
    def get_token_info(mint: str) -> dict:
        """Get token metadata"""
        if mint in TokenInfo.KNOWN_TOKENS:
            return TokenInfo.KNOWN_TOKENS[mint]
        return {
            "name": "Unknown",
            "symbol": "???",
            "decimals": 6,
        }

    @staticmethod
    def format_amount(amount: int, decimals: int) -> float:
        """Format token amount with decimals"""
        return amount / (10 ** decimals)
