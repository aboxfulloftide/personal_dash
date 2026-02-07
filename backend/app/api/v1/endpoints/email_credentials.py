from fastapi import APIRouter, HTTPException, status
from imapclient import IMAPClient

from app.api.v1.deps import CurrentActiveUser, DbSession
from app.crud.email_credential import (
    get_email_credential,
    get_email_credentials,
    get_email_credential_by_id,
    create_email_credential,
    update_email_credential,
    delete_email_credential,
)
from app.core.encryption import decrypt_password
from app.crud.package import create_package, get_packages
from app.api.v1.endpoints.email_scanner import scan_imap_email
from app.schemas.email_credential import (
    EmailCredentialCreate,
    EmailCredentialUpdate,
    EmailCredentialResponse,
    EmailCredentialTestRequest,
    EmailCredentialTestResponse,
)
from app.schemas.package import PackageCreate
from app.crud.email_credential import update_scan_status

router = APIRouter(prefix="/email-credentials", tags=["Email Credentials"])


@router.get("", response_model=list[EmailCredentialResponse])
def get_credentials_list(
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get all email credentials for the current user (passwords are not returned)."""
    credentials = get_email_credentials(db, current_user.id)
    return [EmailCredentialResponse.model_validate(cred) for cred in credentials]


@router.get("/{credential_id}", response_model=EmailCredentialResponse)
def get_credential_by_id(
    credential_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get a specific email credential by ID (password is not returned)."""
    credential = get_email_credential_by_id(db, credential_id, current_user.id)
    if not credential:
        raise HTTPException(status_code=404, detail="Email credential not found")

    return EmailCredentialResponse.model_validate(credential)


@router.post("", response_model=EmailCredentialResponse, status_code=status.HTTP_201_CREATED)
def save_credentials(
    credential_in: EmailCredentialCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Add a new email credential for auto-scanning packages."""
    credential = create_email_credential(db, current_user.id, credential_in)
    return EmailCredentialResponse.model_validate(credential)


@router.put("/{credential_id}", response_model=EmailCredentialResponse)
def update_credentials(
    credential_id: int,
    credential_in: EmailCredentialUpdate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Update a specific email credential."""
    credential = get_email_credential_by_id(db, credential_id, current_user.id)
    if not credential:
        raise HTTPException(status_code=404, detail="Email credential not found")

    updated = update_email_credential(db, credential, credential_in)
    return EmailCredentialResponse.model_validate(updated)


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_credentials(
    credential_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete a specific email credential."""
    credential = get_email_credential_by_id(db, credential_id, current_user.id)
    if not credential:
        raise HTTPException(status_code=404, detail="Email credential not found")

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


@router.post("/{credential_id}/scan", response_model=dict)
async def manual_scan(
    credential_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """
    Manually trigger an email scan for a specific email account.
    Scans email for tracking numbers and adds new packages.
    """
    # Get stored credentials
    credential = get_email_credential_by_id(db, credential_id, current_user.id)
    if not credential:
        raise HTTPException(
            status_code=404,
            detail="Email credential not found."
        )

    if not credential.enabled:
        raise HTTPException(
            status_code=400,
            detail="Email scanning is disabled for this account. Enable it in settings first."
        )

    try:
        # Decrypt password
        password = decrypt_password(credential.encrypted_password)

        # Scan email
        scan_result = await scan_imap_email(
            imap_server=credential.imap_server,
            imap_port=credential.imap_port,
            email_address=credential.email_address,
            password=password,
            days_back=credential.days_to_scan,
        )

        # Get existing packages for this user
        existing_packages = get_packages(db, current_user.id, include_delivered=False)
        existing_tracking_numbers = {pkg.tracking_number.upper() for pkg in existing_packages}

        packages_added = 0

        # Add new packages
        for tracking_info in scan_result.tracking_numbers:
            tracking_number = tracking_info.tracking_number

            # Skip if already tracking
            if tracking_number.upper() in existing_tracking_numbers:
                continue

            # Create package
            try:
                package_data = PackageCreate(
                    tracking_number=tracking_number,
                    carrier=tracking_info.carrier.lower(),
                    description=f"Auto: {tracking_info.found_in_subject[:50]}",
                    status="in_transit",
                )
                create_package(db, current_user.id, package_data)
                packages_added += 1
            except Exception as e:
                # Log error but continue
                print(f"Failed to create package: {e}")

        # Update scan status
        update_scan_status(
            db,
            credential,
            status="success",
            message=f"Found {len(scan_result.tracking_numbers)} tracking numbers",
            packages_found=packages_added,
        )

        return {
            "success": True,
            "emails_scanned": scan_result.emails_scanned,
            "tracking_numbers_found": len(scan_result.tracking_numbers),
            "packages_added": packages_added,
        }

    except HTTPException:
        raise
    except Exception as e:
        # Update scan status with error
        update_scan_status(
            db,
            credential,
            status="error",
            message=str(e)[:500],
            packages_found=0,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scan email: {str(e)}"
        )
