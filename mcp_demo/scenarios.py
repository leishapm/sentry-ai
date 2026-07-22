"""The three pitch-deck demo scenarios, run against the live SENTRY API and a real
MCP tool server. Run with:

    python -m mcp_demo.scenarios

Requires the SENTRY API running first (see README).
"""

import asyncio

import httpx

from mcp_demo.agent import SentryMCPAgent

AGENT_NAME = "Sales Assistant"
ALLOWED_SCOPES = ["inventory_read", "customer_read", "customer_write"]


def _print(title: str, outcome) -> None:
    r = outcome.response
    print(f"\n=== {title} ===")
    print(f"Action:   {outcome.request['action']}")
    print(f"Decision: {r['decision']}  (risk_score={r['risk_score']}, confidence={r['confidence_score']})")
    print(f"Reason:   {r['reason']}")
    if r.get("violated_policy"):
        print(f"Policy violated: {r['violated_policy']}")
    if r.get("suggested_fix"):
        print(f"Suggested fix:   {r['suggested_fix']}")
    if outcome.tool_result is not None:
        print(f"Tool result (via real MCP call): {outcome.tool_result}")


async def main() -> None:
    async with httpx.AsyncClient(timeout=30) as http_client:
        async with SentryMCPAgent.connect(http_client) as agent:
            outcome = await agent.propose(
                "read_inventory",
                {"sku": "SKU-1024"},
                agent_name=AGENT_NAME,
                action="Check inventory for SKU-1024",
                requested_scope="inventory_read",
                allowed_scopes=ALLOWED_SCOPES,
            )
            _print("Scenario 1: safe database read", outcome)

            outcome = await agent.propose(
                "update_pricing",
                {"sku": "SKU-1024", "new_price": 0.01},
                agent_name=AGENT_NAME,
                action="Change the listed price of SKU-1024 to $0.01",
                requested_scope="pricing_write",
                allowed_scopes=ALLOWED_SCOPES,
                is_irreversible=True,
            )
            _print("Scenario 2: unauthorized write", outcome)

            outcome = await agent.propose(
                "delete_customer",
                {"customer_id": 134},
                agent_name=AGENT_NAME,
                action="Delete customer record 134",
                requested_scope="customer_write",
                allowed_scopes=ALLOWED_SCOPES,
                is_irreversible=True,
            )
            _print("Scenario 3: destructive delete", outcome)


if __name__ == "__main__":
    asyncio.run(main())
