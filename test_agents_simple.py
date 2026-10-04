#!/usr/bin/env python3
"""
Simple agent test without full orchestrator dependencies
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from openswarm.agents.solana_audit_agent import SolanaAuditAgent
from openswarm.agents.solana_defi_agent import SolanaDeFiAgent
from openswarm.agents.solana_execution_agent import SolanaExecutionAgent

# Mock contract
VULNERABLE_CONTRACT = """
#[program]
pub mod vulnerable_contract {
    use anchor_lang::prelude::*;

    #[account]
    pub struct Vault {
        pub balance: u64,
        pub owner: Pubkey,
    }

    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        // VULNERABILITY: Integer overflow - no check!
        ctx.accounts.vault.balance -= amount;

        // VULNERABILITY: No access control!
        anchor_lang::system_program::transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                anchor_lang::system_program::Transfer {
                    from: ctx.accounts.user.to_account_info(),
                    to: ctx.accounts.vault.to_account_info(),
                },
            ),
            amount,
        )?;

        Ok(())
    }
}
"""


async def test_audit_agent():
    """Test audit agent"""
    print("\n" + "="*60)
    print("TEST 1: Audit Agent")
    print("="*60)

    agent = SolanaAuditAgent(mock_mode=True)

    context = {
        "contract_code": VULNERABLE_CONTRACT,
        "contract_address": "11111111111111111111111111111111",
    }

    print("\n[Running audit...]")
    result = await agent.execute("Audit contract", context)

    print("\n✅ Audit Complete")
    print(f"Status: {result.get('status')}")
    print(f"\nFindings:\n{result.get('findings', 'No findings')[:500]}")

    return result


async def test_defi_agent():
    """Test DeFi agent"""
    print("\n" + "="*60)
    print("TEST 2: DeFi Agent")
    print("="*60)

    agent = SolanaDeFiAgent(mock_mode=True)

    context = {
        "wallet_address": "So11111111111111111111111111111111111111112",
        "positions": {"SOL": 100, "USDC": 50000, "mSOL": 80},
        "action": "analyze",
    }

    print("\n[Analyzing positions...]")
    result = await agent.execute("Analyze positions", context)

    print("\n✅ DeFi Analysis Complete")
    print(f"Status: {result.get('status')}")
    print(f"\nRecommendation:\n{result.get('recommendation', 'No recommendation')[:500]}")

    return result


async def test_execution_agent():
    """Test execution agent"""
    print("\n" + "="*60)
    print("TEST 3: Execution Agent")
    print("="*60)

    agent = SolanaExecutionAgent()

    context = {
        "action_type": "swap",
        "params": {
            "from": "SOL",
            "to": "USDC",
            "amount": 10,
        },
    }

    print("\n[Building transaction...]")
    result = await agent.execute("Build transaction", context)

    print("\n✅ Transaction Prepared")
    print(f"Status: {result.get('status')}")
    print(f"\nTransaction:\n{result.get('transaction', 'No transaction')}")

    return result


async def main():
    """Run all tests"""
    print("\n🚀 Solana Swarm - Agent Integration Test")
    print("="*60)

    results = {}

    try:
        print("\n[Test 1/3] Audit Agent...")
        results['audit'] = await test_audit_agent()
    except Exception as e:
        print(f"\n❌ Audit test failed: {e}")
        import traceback
        traceback.print_exc()

    try:
        print("\n[Test 2/3] DeFi Agent...")
        results['defi'] = await test_defi_agent()
    except Exception as e:
        print(f"\n❌ DeFi test failed: {e}")
        import traceback
        traceback.print_exc()

    try:
        print("\n[Test 3/3] Execution Agent...")
        results['execution'] = await test_execution_agent()
    except Exception as e:
        print(f"\n❌ Execution test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("✅ All Tests Complete")
    print("="*60)

    # Summary
    print("\n📊 Summary:")
    for agent, result in results.items():
        status = result.get('status', 'unknown')
        print(f"  {agent.upper()}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
