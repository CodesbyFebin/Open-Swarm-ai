"""
Solana Execution Agent
Handles transaction building and execution with approval gates
"""

import json
from typing import Any
from anthropic import Anthropic
from .base import BaseAgent


class SolanaExecutionAgent(BaseAgent):
    """Specialist agent for transaction execution and signing"""

    def __init__(self):
        super().__init__(
            agent_id="solana_execution_agent",
            agent_type="solana_execution"
        )
        self.client = Anthropic()

    async def execute(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Prepare transaction for execution (requires human approval)"""

        action_type = context.get("action_type", "")
        params = context.get("params", {})

        if action_type == "swap":
            return await self._build_swap_tx(params)
        elif action_type == "stake":
            return await self._build_stake_tx(params)
        elif action_type == "unstake":
            return await self._build_unstake_tx(params)

        return {"status": "error", "message": "Unknown action"}

    async def _build_swap_tx(self, params: dict) -> dict[str, Any]:
        """Build swap transaction"""

        tx = {
            "type": "swap",
            "from_token": params.get("from", ""),
            "to_token": params.get("to", ""),
            "amount": params.get("amount", 0),
            "program": "Jupiter",  # DEX aggregator
            "slippage": "1%",
            "status": "pending_approval",
        }

        self.write("pending_transaction", tx)

        return {
            "status": "pending_approval",
            "transaction": tx,
            "requires_signature": True,
        }

    async def _build_stake_tx(self, params: dict) -> dict[str, Any]:
        """Build staking transaction"""

        tx = {
            "type": "stake",
            "pool": params.get("pool", ""),
            "amount": params.get("amount", 0),
            "expected_apy": params.get("apy", 0),
            "status": "pending_approval",
        }

        self.write("pending_transaction", tx)

        return {
            "status": "pending_approval",
            "transaction": tx,
            "requires_signature": True,
        }

    async def _build_unstake_tx(self, params: dict) -> dict[str, Any]:
        """Build unstaking transaction"""

        tx = {
            "type": "unstake",
            "pool": params.get("pool", ""),
            "amount": params.get("amount", 0),
            "unlock_schedule": "immediate",
            "status": "pending_approval",
        }

        self.write("pending_transaction", tx)

        return {
            "status": "pending_approval",
            "transaction": tx,
            "requires_signature": True,
        }
