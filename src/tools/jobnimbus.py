"""JobNimbus API client for fetching contacts."""

from __future__ import annotations

import httpx

from src.config import settings


class JobNimbusError(Exception):
    """Base exception for JobNimbus API errors."""

    pass


class JobNimbusClient:
    """Client for interacting with JobNimbus API."""

    BASE_URL = "https://app.jobnimbus.com/api1"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.jobnimbus_api_key
        if not self.api_key:
            raise ValueError("JobNimbus API key is required")

    async def get_contacts(self) -> list[dict]:
        """
        Fetch all contacts from JobNimbus.

        Returns:
            List of contacts with id, name, and location info.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/contacts",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 401:
                raise JobNimbusError("Invalid API key")
            elif response.status_code == 429:
                raise JobNimbusError("Rate limit exceeded")

            response.raise_for_status()
            data = response.json()

            # Normalize contact data for our use case
            contacts = []
            for contact in data.get("results", data if isinstance(data, list) else []):
                # Handle different name formats
                name = contact.get("display_name") or ""
                if not name:
                    first = contact.get("first_name", "")
                    last = contact.get("last_name", "")
                    name = f"{first} {last}".strip()

                contacts.append(
                    {
                        "id": contact.get("jnid") or contact.get("id", ""),
                        "name": name,
                        "address": contact.get("address_line1")
                        or contact.get("address", ""),
                        "city": contact.get("city", ""),
                        "state": contact.get("state_text") or contact.get("state", ""),
                        "zip": contact.get("zip", ""),
                    }
                )

            return contacts


def get_jobnimbus_client() -> JobNimbusClient:
    """Factory function to get a JobNimbus client instance."""
    return JobNimbusClient()
