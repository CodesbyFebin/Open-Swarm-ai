"""
Solana Smart Contract Audit Agent
Analyzes Anchor programs for security vulnerabilities
"""

from typing import Any
from anthropic import Anthropic
from .base import BaseAgent


class SolanaAuditAgent(BaseAgent):
    """Specialist agent for smart contract security auditing"""

    def __init__(self):
        super().__init__(
            agent_id="solana_audit_agent",
            agent_type="solana_audit"
        )
        self.client = Anthropic()

        self.tools = [
            {
                "name": "parse_contract",
                "description": "Parse Rust smart contract code for structure analysis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "contract_code": {"type": "string", "description": "Contract source code"},
                    },
                    "required": ["contract_code"],
                },
            },
            {
                "name": "identify_vulnerabilities",
                "description": "Identify security vulnerabilities in contract",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "contract_code": {"type": "string"},
                        "patterns": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["contract_code"],
                },
            },
        ]

    async def execute(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Audit a Solana smart contract"""

        # Extract contract from context
        contract_code = context.get("contract_code", "")
        contract_address = context.get("contract_address", "unknown")

        if not contract_code:
            return {
                "status": "error",
                "message": "No contract code provided",
            }

        # Use Claude to analyze contract
        prompt = f"""Analyze this Solana/Anchor smart contract for security vulnerabilities.

Contract Address: {contract_address}
Contract Code:
```rust
{contract_code}
```

Identify:
1. Critical vulnerabilities (overflow, access control, reentrancy)
2. High-risk patterns
3. Medium/low findings
4. Suggested fixes with code examples
5. Overall risk score (1-10)

Be specific with line numbers and exploitation scenarios."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        analysis = response.content[0].text if response.content else "No analysis"

        # Write to blackboard
        self.write("audit_findings", {
            "contract_address": contract_address,
            "analysis": analysis,
            "status": "complete",
        })

        return {
            "status": "success",
            "contract_address": contract_address,
            "findings": analysis,
        }
