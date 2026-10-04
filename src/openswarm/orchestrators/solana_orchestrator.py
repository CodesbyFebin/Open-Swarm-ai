"""
Solana Orchestrator
LangGraph-based swarm for contract auditing + DeFi optimization
"""

import asyncio
from typing import Any, TypedDict
from datetime import datetime

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from ..core.blackboard import get_blackboard
from ..core.router import get_router
from ..agents.solana_audit_agent import SolanaAuditAgent
from ..agents.solana_defi_agent import SolanaDeFiAgent
from ..agents.solana_execution_agent import SolanaExecutionAgent


class SolanaSwarmState(TypedDict):
    """Solana-specific state for LangGraph workflow"""
    user_input: str
    task_type: str  # audit, defi, both
    contract_address: str
    contract_code: str
    wallet_address: str
    positions: dict
    audit_findings: dict
    defi_analysis: dict
    rebalance_plan: dict
    pending_transactions: list
    audit_approved: bool
    defi_approved: bool
    execution_approved: bool
    workflow_stage: str
    agent_outputs: dict[str, Any]
    metadata: dict[str, Any]


def _decide(payload: Any) -> tuple[bool, str | None]:
    """Normalize approval decision"""
    if isinstance(payload, dict):
        return bool(payload.get("approved")), payload.get("reason")
    return bool(payload), None


class SolanaOrchestrator:
    """Multi-agent swarm for Solana intelligence"""

    def __init__(self):
        self.router = get_router()
        self.blackboard = get_blackboard()

        # Initialize agents
        self.audit_agent = SolanaAuditAgent()
        self.defi_agent = SolanaDeFiAgent()
        self.execution_agent = SolanaExecutionAgent()

        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build LangGraph workflow: Route → [Parallel: Audit + DeFi] → Gates → Execute"""
        builder = StateGraph(SolanaSwarmState)

        # Nodes
        builder.add_node("classify", self.classify_node)
        builder.add_node("audit", self.audit_node)
        builder.add_node("defi", self.defi_node)
        builder.add_node("audit_gate", self.audit_gate_node)
        builder.add_node("defi_gate", self.defi_gate_node)
        builder.add_node("synthesis", self.synthesis_node)
        builder.add_node("execution", self.execution_node)
        builder.add_node("final_gate", self.final_gate_node)

        # Edges
        builder.set_entry_point("classify")

        # Classify → Route to audit/defi/both
        builder.add_conditional_edges(
            "classify",
            self._route_by_task_type,
            {
                "audit_only": "audit",
                "defi_only": "defi",
                "both": "audit",  # Start audit, defi runs in parallel
            }
        )

        # Audit flow
        builder.add_edge("audit", "audit_gate")
        builder.add_conditional_edges(
            "audit_gate",
            lambda s: "continue" if s.get("audit_approved") else "abort",
            {"continue": "defi" if s.get("task_type") == "both" else "synthesis",
             "abort": END}
        )

        # DeFi flow (parallel or sequential)
        builder.add_edge("defi", "defi_gate")
        builder.add_conditional_edges(
            "defi_gate",
            lambda s: "continue" if s.get("defi_approved") else "abort",
            {"continue": "synthesis", "abort": END}
        )

        # Synthesis → Execution → Final Gate
        builder.add_edge("synthesis", "execution")
        builder.add_edge("execution", "final_gate")
        builder.add_conditional_edges(
            "final_gate",
            lambda s: "end" if s.get("execution_approved") else "abort",
            {"end": END, "abort": END}
        )

        memory = MemorySaver()
        return builder.compile(checkpointer=memory)

    def _route_by_task_type(self, state: SolanaSwarmState) -> str:
        """Route based on task classification"""
        return state.get("task_type", "audit_only")

    async def classify_node(self, state: SolanaSwarmState) -> dict[str, Any]:
        """Classify user input as audit/defi/both"""
        user_input = state.get("user_input", "")

        # Simple heuristic classification
        audit_keywords = ["audit", "security", "vulnerability", "contract"]
        defi_keywords = ["yield", "optimize", "portfolio", "stake", "defi"]

        is_audit = any(kw in user_input.lower() for kw in audit_keywords)
        is_defi = any(kw in user_input.lower() for kw in defi_keywords)

        if is_audit and is_defi:
            task_type = "both"
        elif is_defi:
            task_type = "defi_only"
        else:
            task_type = "audit_only"

        print(f"[Classifier] Task type: {task_type}")

        return {
            "task_type": task_type,
            "workflow_stage": "classified",
            "metadata": {**state.get("metadata", {}), "classified_at": datetime.now().isoformat()},
        }

    async def audit_node(self, state: SolanaSwarmState) -> dict[str, Any]:
        """Run audit agent"""
        print("[Audit Agent] Analyzing contract...")

        context = {
            "contract_code": state.get("contract_code", ""),
            "contract_address": state.get("contract_address", ""),
        }

        result = await self.audit_agent.execute("Audit contract", context)

        return {
            "audit_findings": result,
            "agent_outputs": {**state.get("agent_outputs", {}), "audit": result},
            "workflow_stage": "audit_complete",
        }

    async def defi_node(self, state: SolanaSwarmState) -> dict[str, Any]:
        """Run DeFi agent"""
        print("[DeFi Agent] Analyzing positions...")

        context = {
            "wallet_address": state.get("wallet_address", ""),
            "positions": state.get("positions", {}),
            "action": "analyze",
        }

        result = await self.defi_agent.execute("Analyze positions", context)

        return {
            "defi_analysis": result,
            "agent_outputs": {**state.get("agent_outputs", {}), "defi": result},
            "workflow_stage": "defi_complete",
        }

    async def audit_gate_node(self, state: SolanaSwarmState) -> dict[str, Any]:
        """Human approval gate for audit findings"""
        findings = state.get("audit_findings", {})

        decision = interrupt({
            "type": "approval",
            "gate": "audit",
            "message": "Review security findings. Approve to continue?",
            "findings": findings,
        })

        approved, reason = _decide(decision)

        if not approved:
            return {
                "audit_approved": False,
                "workflow_stage": "audit_rejected",
            }

        return {
            "audit_approved": True,
            "workflow_stage": "audit_approved",
        }

    async def defi_gate_node(self, state: SolanaSwarmState) -> dict[str, Any]:
        """Human approval gate for DeFi recommendations"""
        analysis = state.get("defi_analysis", {})

        decision = interrupt({
            "type": "approval",
            "gate": "defi",
            "message": "Review yield recommendations. Approve to continue?",
            "analysis": analysis,
        })

        approved, reason = _decide(decision)

        if not approved:
            return {
                "defi_approved": False,
                "workflow_stage": "defi_rejected",
            }

        return {
            "defi_approved": True,
            "workflow_stage": "defi_approved",
        }

    async def synthesis_node(self, state: SolanaSwarmState) -> dict[str, Any]:
        """Combine audit + DeFi insights"""
        print("[Synthesis] Combining findings...")

        synthesis = {
            "audit_findings": state.get("audit_findings"),
            "defi_analysis": state.get("defi_analysis"),
            "combined_insights": "Cross-referenced security + yield strategy",
            "status": "ready_for_execution",
        }

        self.blackboard.write(
            agent_id="synthesis",
            agent_type="synthesizer",
            key="combined_strategy",
            value=synthesis,
        )

        return {
            "agent_outputs": {**state.get("agent_outputs", {}), "synthesis": synthesis},
            "workflow_stage": "synthesized",
        }

    async def execution_node(self, state: SolanaSwarmState) -> dict[str, Any]:
        """Prepare transactions for execution"""
        print("[Execution Agent] Building transactions...")

        # Get recommendations from DeFi analysis
        defi_analysis = state.get("defi_analysis", {})

        if isinstance(defi_analysis, dict) and "plan" in defi_analysis:
            plan = defi_analysis["plan"]

            context = {
                "action_type": "swap",  # Example
                "params": {
                    "from": "SOL",
                    "to": "USDC",
                    "amount": 10,
                },
            }

            result = await self.execution_agent.execute("Build transaction", context)

            return {
                "pending_transactions": [result],
                "agent_outputs": {**state.get("agent_outputs", {}), "execution": result},
                "workflow_stage": "execution_ready",
            }

        return {
            "pending_transactions": [],
            "workflow_stage": "execution_ready",
        }

    async def final_gate_node(self, state: SolanaSwarmState) -> dict[str, Any]:
        """Final approval gate before execution"""
        transactions = state.get("pending_transactions", [])

        decision = interrupt({
            "type": "approval",
            "gate": "execution",
            "message": "Review pending transactions. Approve execution?",
            "transactions": transactions,
        })

        approved, reason = _decide(decision)

        if not approved:
            return {
                "execution_approved": False,
                "workflow_stage": "execution_rejected",
            }

        return {
            "execution_approved": True,
            "workflow_stage": "ready_to_execute",
        }

    async def run(self, user_input: str, context: dict[str, Any] = None) -> dict:
        """Execute the swarm with user input"""
        if context is None:
            context = {}

        initial_state: SolanaSwarmState = {
            "user_input": user_input,
            "task_type": "audit_only",
            "contract_address": context.get("contract_address", ""),
            "contract_code": context.get("contract_code", ""),
            "wallet_address": context.get("wallet_address", ""),
            "positions": context.get("positions", {}),
            "audit_findings": {},
            "defi_analysis": {},
            "rebalance_plan": {},
            "pending_transactions": [],
            "audit_approved": False,
            "defi_approved": False,
            "execution_approved": False,
            "workflow_stage": "initialized",
            "agent_outputs": {},
            "metadata": {"started_at": datetime.now().isoformat()},
        }

        # Execute workflow
        final_state = await asyncio.run(self._execute_workflow(initial_state))

        return final_state

    async def _execute_workflow(self, initial_state: SolanaSwarmState) -> dict:
        """Execute LangGraph workflow"""
        # This is a simplified version - in production would use langgraph streaming
        result = self.workflow.invoke(initial_state)
        return result
