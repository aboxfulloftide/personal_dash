from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.deps import CurrentActiveUser, DbSession
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
