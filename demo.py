#!/usr/bin/env python3
"""
Solana Swarm Demo
Run agent swarms for audit + DeFi optimization
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from openswarm.orchestrators.solana_orchestrator import SolanaOrchestrator
from tests.fixtures import SCENARIOS


async def demo_audit():
    """Demo: Contract audit only"""
    print("\n" + "="*60)
    print("DEMO 1: Smart Contract Audit")
    print("="*60)

    orchestrator = SolanaOrchestrator()
    scenario = SCENARIOS["audit_only"]

    try:
        result = await orchestrator.run(
            user_input=scenario["user_input"],
            context={
                "contract_code": scenario["contract_code"],
                "contract_address": scenario["contract_address"],
            }
        )

        print("\n✅ Audit Complete")
        print(f"Findings: {result.get('audit_findings', {})}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def demo_defi():
    """Demo: DeFi optimization only"""
    print("\n" + "="*60)
    print("DEMO 2: DeFi Yield Optimization")
    print("="*60)

    orchestrator = SolanaOrchestrator()
    scenario = SCENARIOS["defi_only"]

    try:
        result = await orchestrator.run(
            user_input=scenario["user_input"],
            context={
                "wallet_address": scenario["wallet_address"],
                "positions": scenario["positions"],
            }
        )

        print("\n✅ DeFi Analysis Complete")
        print(f"Analysis: {result.get('defi_analysis', {})}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def demo_combined():
    """Demo: Combined audit + DeFi"""
    print("\n" + "="*60)
    print("DEMO 3: Combined Audit + DeFi (Full Intelligence)")
    print("="*60)

    orchestrator = SolanaOrchestrator()
    scenario = SCENARIOS["combined"]

    try:
        result = await orchestrator.run(
            user_input=scenario["user_input"],
            context={
                "contract_code": scenario["contract_code"],
                "contract_address": scenario["contract_address"],
                "wallet_address": scenario["wallet_address"],
                "positions": scenario["positions"],
            }
        )

        print("\n✅ Combined Analysis Complete")
        print(f"Workflow Stage: {result.get('workflow_stage', 'unknown')}")
        print(f"Agent Outputs: {list(result.get('agent_outputs', {}).keys())}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all demos"""
    print("\n🚀 Solana Swarm Intelligence Platform - Demo")
    print("="*60)

    # Test 1: Audit
    try:
        await demo_audit()
    except Exception as e:
        print(f"Audit demo failed: {e}")

    # Test 2: DeFi
    try:
        await demo_defi()
    except Exception as e:
        print(f"DeFi demo failed: {e}")

    # Test 3: Combined
    try:
        await demo_combined()
    except Exception as e:
        print(f"Combined demo failed: {e}")

    print("\n" + "="*60)
    print("✅ Demo Complete")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
