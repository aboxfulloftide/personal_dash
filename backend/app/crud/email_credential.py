from sqlalchemy.orm import Session
from app.models.email_credential import EmailCredential
from app.schemas.email_credential import EmailCredentialCreate, EmailCredentialUpdate
from app.core.encryption import encrypt_password, decrypt_password
from datetime import datetime


def get_email_credential(db: Session, user_id: int) -> EmailCredential | None:
    """Get email credentials for a user."""
    return db.query(EmailCredential).filter(EmailCredential.user_id == user_id).first()


def create_email_credential(
    db: Session,
    user_id: int,
    credential_in: EmailCredentialCreate,
) -> EmailCredential:
    """Create new email credentials for a user."""
    # Encrypt the password
    encrypted_password = encrypt_password(credential_in.password)

    credential = EmailCredential(
        user_id=user_id,
        imap_server=credential_in.imap_server,
        imap_port=credential_in.imap_port,
        email_address=credential_in.email_address,
        encrypted_password=encrypted_password,
        enabled=credential_in.enabled,
        scan_interval_hours=credential_in.scan_interval_hours,
        days_to_scan=credential_in.days_to_scan,
    )

    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential


def update_email_credential(
    db: Session,
    credential: EmailCredential,
    credential_in: EmailCredentialUpdate,
) -> EmailCredential:
    """Update email credentials."""
    update_data = credential_in.model_dump(exclude_unset=True)

    # Encrypt password if provided
    if "password" in update_data:
        update_data["encrypted_password"] = encrypt_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(credential, field, value)

    credential.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(credential)
    return credential


def delete_email_credential(db: Session, credential: EmailCredential):
    """Delete email credentials."""
    db.delete(credential)
    db.commit()


def update_scan_status(
    db: Session,
    credential: EmailCredential,
    status: str,
    message: str | None = None,
    packages_found: int = 0,
):
    """Update the last scan status."""
    credential.last_scan_at = datetime.utcnow()
    credential.last_scan_status = status
    credential.last_scan_message = message
    credential.packages_found_last_scan = packages_found
    db.commit()
    db.refresh(credential)


def get_credentials_due_for_scan(db: Session) -> list[EmailCredential]:
    """Get all enabled credentials that are due for scanning."""
    from datetime import timedelta

    now = datetime.utcnow()
    credentials = []

    all_enabled = db.query(EmailCredential).filter(EmailCredential.enabled == True).all()

    for cred in all_enabled:
        # If never scanned, include it
        if cred.last_scan_at is None:
            credentials.append(cred)
            continue

        # Check if enough time has passed since last scan
        time_since_scan = now - cred.last_scan_at
        scan_interval = timedelta(hours=cred.scan_interval_hours)

        if time_since_scan >= scan_interval:
            credentials.append(cred)

    return credentials
