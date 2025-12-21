import os
import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Databricks Genie")

DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST", "https://bmt-deep-ci-2.cloud.databricks.com")
DATABRICKS_TOKEN = os.environ["DATABRICKS_TOKEN"]
GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "01f0db00369b103d909729dd2bbfb6b6")


@mcp.tool()
async def ask_genie(question: str) -> str:
    """Ask a natural language question about your data using Databricks Genie."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Start conversation
        response = await client.post(
            f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/start-conversation",
            headers={"Authorization": f"Bearer {DATABRICKS_TOKEN}"},
            json={"content": question}
        )
        response.raise_for_status()
        data = response.json()

        conversation_id = data["conversation_id"]
        message_id = data["message_id"]

        # Poll for completion
        for _ in range(60):  # Max 60 attempts
            status_response = await client.get(
                f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/conversations/{conversation_id}/messages/{message_id}",
                headers={"Authorization": f"Bearer {DATABRICKS_TOKEN}"}
            )
            status_response.raise_for_status()
            result = status_response.json()

            status = result.get("status")

            if status == "COMPLETED":
                # Extract the response
                attachments = result.get("attachments", [])
                if attachments:
                    # Get query result if available
                    for att in attachments:
                        if att.get("type") == "QUERY_RESULT":
                            query_id = att.get("query", {}).get("query_id")
                            if query_id:
                                query_result = await client.get(
                                    f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/conversations/{conversation_id}/messages/{message_id}/query-result/{query_id}",
                                    headers={"Authorization": f"Bearer {DATABRICKS_TOKEN}"}
                                )
                                return query_result.text
                        elif att.get("type") == "TEXT":
                            return att.get("text", {}).get("content", "No response content")
                return "Query completed but no results returned"

            elif status == "FAILED":
                return f"Query failed: {result.get('error', 'Unknown error')}"

            # Wait before polling again
            await asyncio.sleep(2)

        return "Query timed out after 120 seconds"


if __name__ == "__main__":
    mcp.run()