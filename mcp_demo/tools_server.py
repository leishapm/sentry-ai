"""Real MCP server exposing the mock enterprise tools SENTRY protects in the demo.

Deliberately dumb: this server has no knowledge of SENTRY, roles, or policy - it just
executes whatever tool call it receives. All safety decisions happen in agent.py, which
calls the live SENTRY API (POST /execute) before a call ever reaches this server.

Run standalone with `python -m mcp_demo.tools_server`, or let agent.py spawn it.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sentry-demo-tools")


@mcp.tool()
def read_inventory(sku: str) -> dict:
    """Read the current stock quantity for a SKU."""
    return {"sku": sku, "quantity": 42}


@mcp.tool()
def delete_customer(customer_id: int) -> dict:
    """Permanently delete a customer record."""
    return {"deleted": customer_id}


@mcp.tool()
def update_pricing(sku: str, new_price: float) -> dict:
    """Change the listed price of a SKU."""
    return {"sku": sku, "new_price": new_price}


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email on behalf of the company."""
    return {"sent_to": to, "subject": subject}


@mcp.tool()
def make_payment(amount_usd: float, recipient: str) -> dict:
    """Send a payment to a recipient."""
    return {"paid": amount_usd, "recipient": recipient}


if __name__ == "__main__":
    mcp.run()
