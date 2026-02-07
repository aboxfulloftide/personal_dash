from fastapi import APIRouter, HTTPException, Query, status, Body
from pydantic import BaseModel

from app.api.v1.deps import CurrentActiveUser, DbSession
from app.api.v1.endpoints.email_scanner import scan_imap_email
from app.crud.package import (
    add_event,
    create_package,
    delete_package,
    get_events,
    get_package_by_id_and_user,
    get_packages,
    update_package,
)
from app.schemas.package import (
    PackageCreate,
    PackageDetail,
    PackageEventCreate,
    PackageEventResponse,
    PackageResponse,
    PackageUpdate,
)

router = APIRouter(prefix="/packages", tags=["Packages"])


@router.post("", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
def create_new_package(
    package_in: PackageCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Add a new package to track."""
    package = create_package(db, current_user.id, package_in)
    return PackageResponse.model_validate(package)


@router.get("", response_model=list[PackageResponse])
def list_packages(
    db: DbSession,
    current_user: CurrentActiveUser,
    include_delivered: bool = Query(False, description="Include delivered packages"),
):
    """List all packages for the current user."""
    packages = get_packages(db, current_user.id, include_delivered)
    return [PackageResponse.model_validate(p) for p in packages]


@router.get("/{package_id}", response_model=PackageDetail)
def get_package_detail(
    package_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get a package with its tracking events."""
    package = get_package_by_id_and_user(db, package_id, current_user.id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    events = get_events(db, package_id)
    return PackageDetail(
        package=PackageResponse.model_validate(package),
        events=[PackageEventResponse.model_validate(e) for e in events],
    )


@router.patch("/{package_id}", response_model=PackageResponse)
def update_package_details(
    package_id: int,
    update_data: PackageUpdate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Update a package's details."""
    package = get_package_by_id_and_user(db, package_id, current_user.id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    updated = update_package(db, package, update_data)
    return PackageResponse.model_validate(updated)


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_package(
    package_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete a package."""
    package = get_package_by_id_and_user(db, package_id, current_user.id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    delete_package(db, package_id)


@router.post("/{package_id}/events", response_model=PackageEventResponse, status_code=status.HTTP_201_CREATED)
def add_tracking_event(
    package_id: int,
    event_in: PackageEventCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Add a tracking event to a package."""
    package = get_package_by_id_and_user(db, package_id, current_user.id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    event = add_event(db, package_id, event_in)
    return PackageEventResponse.model_validate(event)


class EmailScanRequest(BaseModel):
    imap_server: str
    imap_port: int = 993
    email_address: str
    password: str
    days_back: int = 30


class EmailScanResult(BaseModel):
    packages_added: int
    packages_skipped: int  # Already exist
    tracking_numbers_found: list[str]
    emails_scanned: int


@router.post("/scan-email", response_model=EmailScanResult)
async def scan_email_and_add_packages(
    scan_request: EmailScanRequest,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """
    Scan email for tracking numbers and automatically add them as packages.

    For Gmail:
    - imap_server: imap.gmail.com
    - Generate App Password at myaccount.google.com/apppasswords
    - Use the app password, not your regular password

    For Outlook:
    - imap_server: outlook.office365.com

    For Yahoo:
    - imap_server: imap.mail.yahoo.com
    """

    # Scan email for tracking numbers
    scan_result = await scan_imap_email(
        imap_server=scan_request.imap_server,
        imap_port=scan_request.imap_port,
        email_address=scan_request.email_address,
        password=scan_request.password,
        days_back=scan_request.days_back,
    )

    # Get existing package tracking numbers for this user
    existing_packages = get_packages(db, current_user.id, include_delivered=False)
    existing_tracking_numbers = {pkg.tracking_number.upper() for pkg in existing_packages}

    packages_added = 0
    packages_skipped = 0
    tracking_numbers_found = []

    # Add each found tracking number as a package (if not already exists)
    for tracking_info in scan_result.tracking_numbers:
        tracking_number = tracking_info.tracking_number
        tracking_numbers_found.append(tracking_number)

        # Skip if already tracking this package
        if tracking_number.upper() in existing_tracking_numbers:
            packages_skipped += 1
            continue

        # Create package
        try:
            package_data = PackageCreate(
                tracking_number=tracking_number,
                carrier=tracking_info.carrier,
                description=f"Auto-added from email: {tracking_info.found_in_subject[:50]}",
                status="in_transit",
            )
            create_package(db, current_user.id, package_data)
            packages_added += 1
        except Exception:
            # Skip if creation fails (e.g., duplicate tracking number race condition)
            packages_skipped += 1

    return EmailScanResult(
        packages_added=packages_added,
        packages_skipped=packages_skipped,
        tracking_numbers_found=tracking_numbers_found,
        emails_scanned=scan_result.emails_scanned,
    )
