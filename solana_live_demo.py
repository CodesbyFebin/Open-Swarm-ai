#!/usr/bin/env python3
"""
Solana Intelligence Platform - Live Data Demo
Fetches real on-chain data and runs agent analysis
"""

import asyncio
import sys
import os
from typing import Optional
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from openswarm.agents.solana_audit_agent import SolanaAuditAgent
from openswarm.agents.solana_defi_agent import SolanaDeFiAgent
from openswarm.utils.solana_utils import SolanaRPC, DefiDataFetcher, TokenInfo


class SolanaLiveDemo:
    """Live demonstration using real Solana data"""

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc = SolanaRPC(rpc_url)
        self.defi_fetcher = DefiDataFetcher()

    async def close(self):
        """Cleanup resources"""
        await self.rpc.close()
        await self.defi_fetcher.close()

    async def demo_wallet_analysis(self, wallet_address: str):
        """Analyze a real wallet"""
        print(f"\n{'='*70}")
        print(f"LIVE WALLET ANALYSIS: {wallet_address}")
        print(f"{'='*70}\n")

        print("[1/3] Fetching wallet balance...")
        balance_result = await self.rpc.get_balance(wallet_address)

        if "error" in balance_result:
            print(f"❌ Error fetching balance: {balance_result['error']}")
            return

        lamports = balance_result.get("result", {}).get("value", 0)
        sol_balance = lamports / 1e9

        print(f"✓ SOL Balance: {sol_balance:.4f} SOL")

        print("\n[2/3] Fetching token accounts...")
        tokens_result = await self.rpc.get_parsed_token_accounts(wallet_address)

        if "error" not in tokens_result:
            accounts = tokens_result.get("result", {}).get("value", [])
            print(f"✓ Token Accounts: {len(accounts)}")

            for account in accounts[:5]:
                try:
                    parsed = account.get("account", {}).get("data", {}).get("parsed", {})
                    token_amount = parsed.get("info", {}).get("tokenAmount", {})
                    mint = parsed.get("info", {}).get("mint", "unknown")
                    balance = token_amount.get("uiAmount", 0)

                    token_info = TokenInfo.get_token_info(mint)
                    print(f"  - {token_info['symbol']}: {balance}")
                except Exception as e:
                    pass

        print("\n[3/3] Running agent analysis...")
        # Run DeFi agent with real data
        agent = SolanaDeFiAgent(mock_mode=True)  # Use mock for demo safety
        result = await agent.execute("Analyze positions", {
            "wallet_address": wallet_address,
            "positions": {
                "SOL": sol_balance,
                "USDC": 10000,  # Mock for demo
            },
            "action": "analyze"
        })

        print(f"\n✓ Analysis Complete: {result.get('status')}")

    async def demo_defi_data(self):
        """Fetch and display real DeFi pool data"""
        print(f"\n{'='*70}")
        print("LIVE DeFi POOL DATA")
        print(f"{'='*70}\n")

        fetcher = self.defi_fetcher

        print("[1/2] Fetching DeFiLlama pools...")
        pools_result = await fetcher.get_defillama_pools()

        if "pools" in pools_result:
            print(f"✓ Found {pools_result.get('total', 0)} Solana pools\n")

            # Show top 10 by TVL
            top_pools = sorted(
                pools_result.get("pools", []),
                key=lambda p: float(p.get("tvlUsd", 0)),
                reverse=True
            )[:10]

            print("Top 10 Pools by TVL:")
            print(f"{'Pool':<30} {'APY':<10} {'TVL (M)':<15} {'Risk'}")
            print("-" * 70)

            for pool in top_pools:
                name = pool.get("project", "unknown")[:28]
                apy = float(pool.get("apy", 0))
                tvl = float(pool.get("tvlUsd", 0)) / 1e6
                risk = "HIGH" if apy > 20 else "MED" if apy > 10 else "LOW"

                print(f"{name:<30} {apy:>8.2f}% ${tvl:>13.1f}M {risk}")

        print("\n[2/2] Fetching token prices...")
        # Example mints to fetch
        mints = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWaLb3dMEVzgcMKwW2QKsMwqyqDe6E8W8qYunEqnE",  # USDC
        ]

        prices = await fetcher.get_jupiter_prices(mints)
        if "prices" in prices:
            print(f"✓ Fetched {len(prices['prices'])} token prices")
            for mint, price_data in list(prices['prices'].items())[:5]:
                price = price_data.get("price", 0)
                token = TokenInfo.get_token_info(mint)
                print(f"  {token['symbol']}: ${price:.4f}")

    async def demo_contract_audit(self, contract_address: str):
        """Analyze a real contract if available"""
        print(f"\n{'='*70}")
        print(f"LIVE CONTRACT AUDIT: {contract_address}")
        print(f"{'='*70}\n")

        print("[1/2] Fetching contract account info...")
        account_info = await self.rpc.get_account_info(contract_address)

        if "error" in account_info:
            print(f"❌ Error fetching account: {account_info['error']}")
            return

        result = account_info.get("result")
        if not result:
            print("❌ Account not found")
            return

        executable = result.get("executable", False)
        owner = result.get("owner", "unknown")
        lamports = result.get("lamports", 0)

        print(f"✓ Contract Owner: {owner}")
        print(f"✓ Executable: {executable}")
        print(f"✓ Account Balance: {lamports / 1e9:.4f} SOL")

        # Try to decode contract data
        data = result.get("data", ["", "base64"])
        print(f"\n[2/2] Analyzing contract structure...")
        print(f"✓ Program Size: {len(data[0]) * 3 / 4 / 1024:.1f} KB")

        print("\nNote: Full contract code audit requires Solscan/GitHub integration")

    async def demo_portfolio_optimization(self):
        """Demo portfolio optimization workflow"""
        print(f"\n{'='*70}")
        print("PORTFOLIO OPTIMIZATION WORKFLOW")
        print(f"{'='*70}\n")

        # Example portfolio
        portfolio = {
            "SOL": 100,
            "USDC": 50000,
            "mSOL": 80,
        }

        print("Portfolio:")
        for token, amount in portfolio.items():
            print(f"  {token}: {amount}")

        print("\n[1/2] Fetching current yields...")
        agent = SolanaDeFiAgent(mock_mode=True, use_real_data=False)

        analysis = await agent.execute("Analyze", {
            "wallet_address": "example_wallet",
            "positions": portfolio,
            "action": "analyze"
        })

        print(f"✓ Analysis complete")
        print(f"\nRecommendations:")
        recommendation = analysis.get("recommendation", "")
        # Show first 500 chars
        print(recommendation[:500] + "...")

        print("\n[2/2] Transaction simulation...")
        print("Simulated transactions ready (awaiting approval)")

    async def run_all_demos(self):
        """Run all live demos"""
        print("\n" + "🚀" + "="*68 + "🚀")
        print("  SOLANA INTELLIGENCE PLATFORM - LIVE DATA DEMONSTRATION")
        print("🚀" + "="*68 + "🚀")

        try:
            # Demo 1: Portfolio optimization
            print("\n📊 DEMO 1: Portfolio Optimization")
            await self.demo_portfolio_optimization()

            # Demo 2: DeFi data (requires network)
            print("\n📊 DEMO 2: Live DeFi Pool Data")
            try:
                await self.demo_defi_data()
            except Exception as e:
                print(f"⚠️  Could not fetch live data: {e}")
                print("   (Network access may be restricted)")

            # Demo 3: Wallet analysis with mock data
            print("\n📊 DEMO 3: Wallet Analysis")
            demo_wallet = "So11111111111111111111111111111111111111112"
            try:
                await self.demo_wallet_analysis(demo_wallet)
            except Exception as e:
                print(f"⚠️  Could not fetch wallet data: {e}")
                print("   (Network access may be restricted)")

            print("\n" + "="*70)
            print("✅ LIVE DEMONSTRATIONS COMPLETE")
            print("="*70)
            print("""
Next steps for production:
1. Set up real Solana RPC endpoint (e.g., from Helius, Alchemy)
2. Authenticate with DeFi APIs (Jupiter, DeFiLlama)
3. Implement transaction signing with Solana.py
4. Add Web3 wallet integration (Phantom, Solflare)
5. Deploy as service with API endpoints
6. Add WebSocket for real-time data
""")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await self.close()


async def main():
    demo = SolanaLiveDemo()
    try:
        await demo.run_all_demos()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await demo.close()


if __name__ == "__main__":
    asyncio.run(main())
