from datetime import datetime
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

    # If marking as delivered, set delivered_at timestamp (use local time for midnight calculations)
    if update_data.delivered is True and package.delivered_at is None:
        package.delivered_at = datetime.now()  # Local time, not UTC

    db.commit()
    db.refresh(package)
    return package


def delete_delivered_packages(db: Session, user_id: int) -> int:
    """Soft delete all delivered packages for a user. Returns count deleted."""
    result = db.execute(
        select(Package).where(
            Package.user_id == user_id,
            Package.delivered == True,
            Package.dismissed == False,
        )
    )
    packages = list(result.scalars().all())
    now = datetime.now()
    for package in packages:
        package.dismissed = True
        package.dismissed_at = now
    db.commit()
    return len(packages)


def delete_package(db: Session, package_id: int) -> bool:
    """Soft delete a package (marks as dismissed). Returns True if deleted."""
    package = db.get(Package, package_id)
    if not package:
        return False
    # Soft delete: mark as dismissed instead of hard deleting
    package.dismissed = True
    package.dismissed_at = datetime.now()  # Local time, not UTC
    db.commit()
    return True


def add_event(db: Session, package_id: int, event_in: PackageEventCreate) -> PackageEvent:
    """Add a tracking event to a package."""
    event = PackageEvent(
        package_id=package_id,
        status=event_in.status,
        location=event_in.location,
        event_time=event_in.event_time or datetime.now(),  # Local time, not UTC
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
    tracking_number: str,
    delivery_subject: str = None,
    delivery_sender: str = None,
) -> Package | None:
    """
    Find a package by tracking number and mark it as delivered.
    Falls back through three matching strategies if no exact tracking match is found:
      1. Subject similarity (threshold 0.4, or 0.25 when sender domain matches)
      2. Unique candidate from same sender domain
      3. Best subject match among same-sender candidates (threshold 0.15)
    Returns the updated package if found, None otherwise.
    """
    import re

    print(f"[DEBUG] Attempting to mark package delivered:")
    print(f"  User ID: {user_id}")
    print(f"  Tracking number: {tracking_number}")
    print(f"  Delivery subject: {delivery_subject}")
    print(f"  Delivery sender: {delivery_sender}")

    # Case-insensitive search for tracking number (skip empty string)
    packages = []
    if tracking_number:
        result = db.execute(
            select(Package).where(
                Package.user_id == user_id,
                Package.tracking_number.ilike(tracking_number),
                Package.dismissed == False,
            )
        )
        packages = list(result.scalars().all())

    # Fuzzy fallback: subject similarity + sender domain matching
    if not packages and (delivery_subject or delivery_sender):
        print(f"  ℹ No exact tracking match, trying fuzzy matching...")

        from app.core.scheduler import calculate_subject_similarity
        from datetime import timedelta

        two_weeks_ago = datetime.now() - timedelta(days=14)

        result = db.execute(
            select(Package).where(
                Package.user_id == user_id,
                Package.dismissed == False,
                Package.delivered == False,
                Package.created_at >= two_weeks_ago,
            )
        )
        candidate_packages = list(result.scalars().all())

        print(f"  Checking {len(candidate_packages)} undelivered packages")

        # Extract sender domain (e.g. "amazon.com" from "Ship <ship@amazon.com>")
        sender_domain = None
        if delivery_sender:
            m = re.search(r'@([\w.-]+)', delivery_sender)
            if m:
                sender_domain = m.group(1).lower()

        # --- Stage 1: Subject similarity ---
        best_match = None
        best_similarity = 0.0

        for pkg in candidate_packages:
            if not pkg.email_subject or not delivery_subject:
                continue
            similarity = calculate_subject_similarity(pkg.email_subject, delivery_subject)
            same_sender = bool(sender_domain and pkg.email_sender and sender_domain in pkg.email_sender.lower())
            print(f"    Package #{pkg.id} '{pkg.email_subject[:50]}' similarity: {similarity:.0%} same_sender={same_sender}")

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = pkg

        if best_match:
            same_sender = bool(sender_domain and best_match.email_sender and sender_domain in best_match.email_sender.lower())
            # Lower threshold when delivery and shipping emails share the same sender domain
            threshold = 0.25 if same_sender else 0.5
            if best_similarity >= threshold:
                print(f"  ✓ Matched by subject similarity ({best_similarity:.0%}, same_sender={same_sender}): {best_match.description}")
                packages = [best_match]
            else:
                print(f"  ✗ Subject similarity too low (best: {best_similarity:.0%}, threshold: {threshold:.0%})")

        # --- Stage 2: Unique candidate from same sender domain ---
        if not packages and sender_domain:
            domain_candidates = [
                p for p in candidate_packages
                if p.email_sender and sender_domain in p.email_sender.lower()
            ]
            if len(domain_candidates) == 1:
                print(f"  ✓ Matched by unique sender domain ({sender_domain}): {domain_candidates[0].description}")
                packages = domain_candidates

            # --- Stage 3: Best subject match among same-sender candidates ---
            elif len(domain_candidates) > 1 and delivery_subject:
                best = max(
                    domain_candidates,
                    key=lambda p: calculate_subject_similarity(p.email_subject or '', delivery_subject),
                )
                sim = calculate_subject_similarity(best.email_subject or '', delivery_subject)
                if sim >= 0.15:
                    print(f"  ✓ Matched by sender domain + weak subject ({sim:.0%}): {best.description}")
                    packages = [best]
                else:
                    print(f"  ✗ No match: sender domain has {len(domain_candidates)} candidates but best subject similarity too low ({sim:.0%})")
            else:
                print(f"  ✗ No match by sender domain ({sender_domain})")

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
                package.delivered_at = datetime.now()  # Local time, not UTC
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
