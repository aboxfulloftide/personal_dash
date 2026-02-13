from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.package import Package, PackageEvent
from app.schemas.package import PackageCreate, PackageUpdate, PackageEventCreate


def create_package(db: Session, user_id: int, package_in: PackageCreate) -> Package:
    """Create a new package."""
    # Determine source based on whether email metadata is present
    source = "email" if package_in.email_source else "manual"

    package = Package(
        user_id=user_id,
        tracking_number=package_in.tracking_number,
        carrier=package_in.carrier.value,
        description=package_in.description,
        source=source,
        email_source=package_in.email_source,
        email_subject=package_in.email_subject,
        email_sender=package_in.email_sender,
        email_date=package_in.email_date,
        email_body_snippet=package_in.email_body_snippet,
        tracking_url=package_in.tracking_url,
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    return package


def get_packages(db: Session, user_id: int, include_delivered: bool = False) -> list[Package]:
    """Get all packages for a user (excludes dismissed packages)."""
    query = select(Package).where(Package.user_id == user_id, Package.dismissed == False)
    if not include_delivered:
        query = query.where(Package.delivered == False)
    query = query.order_by(Package.created_at.desc())
    result = db.execute(query)
    return list(result.scalars().all())


def get_package(db: Session, package_id: int) -> Package | None:
    """Get a package by ID."""
    return db.get(Package, package_id)


def get_package_by_id_and_user(db: Session, package_id: int, user_id: int) -> Package | None:
    """Get a package by ID with ownership check."""
    result = db.execute(
        select(Package).where(Package.id == package_id, Package.user_id == user_id)
    )
    return result.scalar_one_or_none()


def update_package(db: Session, package: Package, update_data: PackageUpdate) -> Package:
    """Update a package."""
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        setattr(package, field, value)

    # If marking as delivered, set delivered_at timestamp
    if update_data.delivered is True and package.delivered_at is None:
        package.delivered_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.commit()
    db.refresh(package)
    return package


def delete_package(db: Session, package_id: int) -> bool:
    """Soft delete a package (marks as dismissed). Returns True if deleted."""
    package = db.get(Package, package_id)
    if not package:
        return False
    # Soft delete: mark as dismissed instead of hard deleting
    package.dismissed = True
    package.dismissed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return True


def add_event(db: Session, package_id: int, event_in: PackageEventCreate) -> PackageEvent:
    """Add a tracking event to a package."""
    event = PackageEvent(
        package_id=package_id,
        status=event_in.status,
        location=event_in.location,
        event_time=event_in.event_time or datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_events(db: Session, package_id: int) -> list[PackageEvent]:
    """Get all events for a package, ordered by event_time descending."""
    result = db.execute(
        select(PackageEvent)
        .where(PackageEvent.package_id == package_id)
        .order_by(PackageEvent.event_time.desc())
    )
    return list(result.scalars().all())


def mark_package_delivered_by_tracking(
    db: Session,
    user_id: int,
    tracking_number: str
) -> Package | None:
    """
    Find a package by tracking number and mark it as delivered.
    Returns the updated package if found, None otherwise.
    """
    print(f"[DEBUG] Attempting to mark package delivered:")
    print(f"  User ID: {user_id}")
    print(f"  Tracking number: {tracking_number}")

    # Case-insensitive search for tracking number
    result = db.execute(
        select(Package).where(
            Package.user_id == user_id,
            Package.tracking_number.ilike(tracking_number),
            Package.dismissed == False,
        )
    )
    packages = list(result.scalars().all())

    if packages:
        if len(packages) > 1:
            print(f"  ⚠ Found {len(packages)} duplicate packages with same tracking number!")

        # Mark all matching packages as delivered (handles duplicates)
        delivered_count = 0
        for package in packages:
            print(f"  ✓ Found package: {package.description}")
            print(f"    Package tracking: {package.tracking_number}")
            print(f"    Already delivered: {package.delivered}")

            if not package.delivered:
                package.delivered = True
                package.delivered_at = datetime.now(timezone.utc).replace(tzinfo=None)
                package.status = "Delivered"
                delivered_count += 1

        if delivered_count > 0:
            db.commit()
            print(f"  ✓ Marked {delivered_count} package(s) as delivered!")
        else:
            print(f"  ⚠ All packages already marked as delivered")

        return packages[0]  # Return first package
    else:
        print(f"  ✗ No matching package found")
        # Show what packages exist for this user
        all_packages = db.execute(
            select(Package).where(
                Package.user_id == user_id,
                Package.dismissed == False,
            )
        ).scalars().all()
        print(f"  Available packages for user {user_id}:")
        for pkg in all_packages:
            print(f"    - {pkg.tracking_number}: {pkg.description}")

    return None
