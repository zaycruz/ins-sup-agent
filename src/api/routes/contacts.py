"""Contact routes for JobNimbus integration."""

from fastapi import APIRouter, HTTPException

from src.tools.jobnimbus import JobNimbusClient, JobNimbusError
from src.config import settings

router = APIRouter()


@router.get("/contacts")
async def list_contacts():
    """
    Fetch all contacts from JobNimbus for dropdown selection.

    Returns a list of contacts with location information.
    """
    if not settings.jobnimbus_api_key:
        raise HTTPException(
            status_code=503,
            detail="JobNimbus integration not configured. Set JOBNIMBUS_API_KEY.",
        )

    try:
        client = JobNimbusClient()
        contacts = await client.get_contacts()
        return contacts
    except JobNimbusError as e:
        raise HTTPException(status_code=502, detail=f"JobNimbus API error: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch contacts: {str(e)}"
        )
