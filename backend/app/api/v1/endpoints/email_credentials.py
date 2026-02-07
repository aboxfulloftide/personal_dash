from fastapi import APIRouter, HTTPException, status
from imapclient import IMAPClient

from app.api.v1.deps import CurrentActiveUser, DbSession
from app.crud.email_credential import (
    get_email_credential,
    create_email_credential,
    update_email_credential,
    delete_email_credential,
)
from app.core.encryption import decrypt_password
from app.schemas.email_credential import (
    EmailCredentialCreate,
    EmailCredentialUpdate,
    EmailCredentialResponse,
    EmailCredentialTestRequest,
    EmailCredentialTestResponse,
)

router = APIRouter(prefix="/email-credentials", tags=["Email Credentials"])


@router.get("", response_model=EmailCredentialResponse | None)
def get_credentials(
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get email credentials for the current user (password is not returned)."""
    credential = get_email_credential(db, current_user.id)
    if not credential:
        return None

    return EmailCredentialResponse.model_validate(credential)


@router.post("", response_model=EmailCredentialResponse, status_code=status.HTTP_201_CREATED)
def save_credentials(
    credential_in: EmailCredentialCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Save email credentials for auto-scanning packages."""
    # Check if credentials already exist
    existing = get_email_credential(db, current_user.id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email credentials already exist. Use PUT to update or DELETE first."
        )

    credential = create_email_credential(db, current_user.id, credential_in)
    return EmailCredentialResponse.model_validate(credential)


@router.put("", response_model=EmailCredentialResponse)
def update_credentials(
    credential_in: EmailCredentialUpdate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Update email credentials."""
    credential = get_email_credential(db, current_user.id)
    if not credential:
        raise HTTPException(status_code=404, detail="Email credentials not found")

    updated = update_email_credential(db, credential, credential_in)
    return EmailCredentialResponse.model_validate(updated)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def remove_credentials(
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete email credentials."""
    credential = get_email_credential(db, current_user.id)
    if not credential:
        raise HTTPException(status_code=404, detail="Email credentials not found")

    delete_email_credential(db, credential)


@router.post("/test", response_model=EmailCredentialTestResponse)
async def test_connection(
    test_request: EmailCredentialTestRequest,
    current_user: CurrentActiveUser,
):
    """
    Test IMAP connection with provided credentials.
    Does not save credentials, just tests connectivity.
    """
    try:
        with IMAPClient(test_request.imap_server, port=test_request.imap_port, ssl=True) as client:
            client.login(test_request.email_address, test_request.password)
            # Try to select inbox to ensure we have access
            client.select_folder('INBOX', readonly=True)

        return EmailCredentialTestResponse(
            success=True,
            message="Successfully connected to email server"
        )

    except Exception as e:
        return EmailCredentialTestResponse(
            success=False,
            message=f"Connection failed: {str(e)}"
        )
