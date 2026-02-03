# Task 011: Package Tracking Widget

## Objective
Build a package tracking widget that supports manual entry and email parsing to track packages from USPS, UPS, FedEx, and Amazon.

## Prerequisites
- Task 003 completed (Database Schema)
- Task 004 completed (Authentication)
- Task 006 completed (Widget Framework)

## Features
- Manual package entry with tracking number
- Automatic carrier detection
- Email parsing for tracking numbers (Gmail and IMAP)
- Status updates via carrier APIs/scraping
- Package history and archiving
- Multi-user support

## Deliverables

### 1. Database Models

#### backend/app/models/package.py:
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class CarrierType(str, enum.Enum):
    USPS = "usps"
    UPS = "ups"
    FEDEX = "fedex"
    AMAZON = "amazon"
    OTHER = "other"


class PackageStatus(str, enum.Enum):
    PENDING = "pending"           # Just added, not yet checked
    PRE_TRANSIT = "pre_transit"   # Label created
    IN_TRANSIT = "in_transit"     # On the way
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"       # Problem with delivery
    UNKNOWN = "unknown"


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Package info
    tracking_number = Column(String(100), nullable=False, index=True)
    carrier = Column(Enum(CarrierType), nullable=False)
    description = Column(String(255), nullable=True)  # User-friendly name

    # Status
    status = Column(Enum(PackageStatus), default=PackageStatus.PENDING)
    status_description = Column(String(255), nullable=True)

    # Location info
    origin = Column(String(255), nullable=True)
    destination = Column(String(255), nullable=True)
    current_location = Column(String(255), nullable=True)

    # Dates
    ship_date = Column(DateTime, nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    actual_delivery = Column(DateTime, nullable=True)

    # Metadata
    source = Column(String(50), default="manual")  # manual, email, api
    email_subject = Column(String(255), nullable=True)  # If from email
    is_archived = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="packages")
    tracking_history = relationship("TrackingEvent", back_populates="package", 
                                    order_by="desc(TrackingEvent.timestamp)")


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)

    timestamp = Column(DateTime, nullable=False)
    status = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    package = relationship("Package", back_populates="tracking_history")


class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    email_address = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)  # gmail, imap

    # For IMAP
    imap_server = Column(String(255), nullable=True)
    imap_port = Column(Integer, default=993)

    # Encrypted credentials (use app-specific passwords)
    encrypted_password = Column(Text, nullable=True)

    # OAuth tokens (for Gmail)
    oauth_token = Column(Text, nullable=True)
    oauth_refresh_token = Column(Text, nullable=True)
    oauth_expiry = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="email_accounts")
```

### 2. Carrier Detection Service

#### backend/app/services/carrier_detection.py:
```python
import re
from typing import Optional, Tuple
from app.models.package import CarrierType


class CarrierDetector:
    """Detect carrier from tracking number format."""

    # Tracking number patterns
    PATTERNS = {
        CarrierType.USPS: [
            # USPS Tracking (22 digits)
            r'^[0-9]{20,22}$',
            # USPS Priority Mail (starts with 94)
            r'^94[0-9]{20,22}$',
            # USPS Certified Mail
            r'^7[0-9]{19,21}$',
            # USPS Express Mail (starts with E)
            r'^E[A-Z][0-9]{9}US$',
            # USPS International
            r'^[A-Z]{2}[0-9]{9}US$',
        ],
        CarrierType.UPS: [
            # UPS Standard (1Z + 16 alphanumeric)
            r'^1Z[A-Z0-9]{16}$',
            # UPS Mail Innovations
            r'^MI[0-9]{6}[A-Z0-9]{1,20}$',
            # UPS Freight
            r'^[HKT][0-9]{10}$',
        ],
        CarrierType.FEDEX: [
            # FedEx Express (12 digits)
            r'^[0-9]{12}$',
            # FedEx Ground (15 digits)
            r'^[0-9]{15}$',
            # FedEx Ground (20-22 digits)
            r'^[0-9]{20,22}$',
            # FedEx SmartPost (22 digits starting with 61)
            r'^61[0-9]{20}$',
            # Door Tag
            r'^DT[0-9]{12}$',
        ],
        CarrierType.AMAZON: [
            # Amazon Logistics (TBA)
            r'^TBA[0-9]{12,}$',
        ],
    }

    @classmethod
    def detect(cls, tracking_number: str) -> Tuple[CarrierType, float]:
        """
        Detect carrier from tracking number.
        Returns (carrier, confidence) where confidence is 0.0-1.0
        """
        # Clean the tracking number
        clean_number = tracking_number.upper().replace(" ", "").replace("-", "")

        for carrier, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, clean_number):
                    return (carrier, 0.95)

        # Try to make educated guesses based on length/format
        if clean_number.startswith("1Z"):
            return (CarrierType.UPS, 0.8)
        if clean_number.startswith("TBA"):
            return (CarrierType.AMAZON, 0.9)
        if len(clean_number) == 12 and clean_number.isdigit():
            return (CarrierType.FEDEX, 0.6)
        if len(clean_number) >= 20 and clean_number.isdigit():
            return (CarrierType.USPS, 0.5)

        return (CarrierType.OTHER, 0.0)

    @classmethod
    def validate(cls, tracking_number: str, carrier: CarrierType) -> bool:
        """Validate tracking number format for a specific carrier."""
        clean_number = tracking_number.upper().replace(" ", "").replace("-", "")

        if carrier not in cls.PATTERNS:
            return True  # Can't validate unknown carriers

        for pattern in cls.PATTERNS[carrier]:
            if re.match(pattern, clean_number):
                return True

        return False
```

### 3. Tracking Service

#### backend/app/services/tracking_service.py:
```python
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

from app.models.package import Package, TrackingEvent, CarrierType, PackageStatus
from app.core.config import settings


class BaseTracker(ABC):
    """Base class for carrier tracking implementations."""

    @abstractmethod
    async def track(self, tracking_number: str) -> Dict[str, Any]:
        """
        Track a package and return status info.

        Returns:
            {
                "status": PackageStatus,
                "status_description": str,
                "current_location": str,
                "estimated_delivery": datetime or None,
                "events": [
                    {
                        "timestamp": datetime,
                        "status": str,
                        "description": str,
                        "location": str
                    }
                ]
            }
        """
        pass


class USPSTracker(BaseTracker):
    """USPS tracking using their API."""

    # USPS Web Tools API (free, requires registration)
    BASE_URL = "https://secure.shippingapis.com/ShippingAPI.dll"

    def __init__(self):
        self.user_id = settings.USPS_USER_ID  # From USPS Web Tools registration

    async def track(self, tracking_number: str) -> Dict[str, Any]:
        if not self.user_id:
            return await self._fallback_track(tracking_number)

        xml_request = f'''
        <TrackFieldRequest USERID="{self.user_id}">
            <TrackID ID="{tracking_number}"></TrackID>
        </TrackFieldRequest>
        '''

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.BASE_URL,
                    params={"API": "TrackV2", "XML": xml_request},
                    timeout=30
                )
                return self._parse_response(response.text)
            except Exception as e:
                return {"status": PackageStatus.UNKNOWN, "error": str(e)}

    def _parse_response(self, xml_text: str) -> Dict[str, Any]:
        # Parse USPS XML response
        # Implementation depends on actual API response format
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(xml_text)
            # Parse tracking info from XML
            # This is simplified - actual implementation needs full parsing

            events = []
            status = PackageStatus.UNKNOWN

            for detail in root.findall(".//TrackDetail"):
                event_text = detail.text or ""
                events.append({
                    "timestamp": datetime.utcnow(),  # Parse from response
                    "status": event_text[:50],
                    "description": event_text,
                    "location": ""
                })

            # Determine status from latest event
            summary = root.find(".//TrackSummary")
            if summary is not None:
                summary_text = summary.text or ""
                if "delivered" in summary_text.lower():
                    status = PackageStatus.DELIVERED
                elif "out for delivery" in summary_text.lower():
                    status = PackageStatus.OUT_FOR_DELIVERY
                elif "in transit" in summary_text.lower():
                    status = PackageStatus.IN_TRANSIT

            return {
                "status": status,
                "status_description": summary.text if summary is not None else "",
                "events": events
            }
        except Exception as e:
            return {"status": PackageStatus.UNKNOWN, "error": str(e)}

    async def _fallback_track(self, tracking_number: str) -> Dict[str, Any]:
        """Fallback when no API key available."""
        return {
            "status": PackageStatus.UNKNOWN,
            "status_description": "USPS API not configured",
            "events": []
        }


class UPSTracker(BaseTracker):
    """UPS tracking implementation."""

    async def track(self, tracking_number: str) -> Dict[str, Any]:
        # UPS requires OAuth2 and paid API access for production
        # For free tier, we can use limited tracking

        # Placeholder - implement based on UPS API access level
        return {
            "status": PackageStatus.UNKNOWN,
            "status_description": "UPS tracking requires API setup",
            "events": []
        }


class FedExTracker(BaseTracker):
    """FedEx tracking implementation."""

    async def track(self, tracking_number: str) -> Dict[str, Any]:
        # FedEx requires API credentials
        # Placeholder implementation
        return {
            "status": PackageStatus.UNKNOWN,
            "status_description": "FedEx tracking requires API setup",
            "events": []
        }


class AmazonTracker(BaseTracker):
    """Amazon tracking - primarily relies on email parsing."""

    async def track(self, tracking_number: str) -> Dict[str, Any]:
        # Amazon doesn't provide public tracking API
        # Status comes from email parsing
        return {
            "status": PackageStatus.UNKNOWN,
            "status_description": "Amazon tracking via email only",
            "events": []
        }


class TrackingService:
    """Main tracking service that coordinates all carriers."""

    def __init__(self):
        self.trackers = {
            CarrierType.USPS: USPSTracker(),
            CarrierType.UPS: UPSTracker(),
            CarrierType.FEDEX: FedExTracker(),
            CarrierType.AMAZON: AmazonTracker(),
        }

    async def track_package(self, package: Package) -> Dict[str, Any]:
        """Track a package and return updated info."""
        tracker = self.trackers.get(package.carrier)

        if not tracker:
            return {
                "status": PackageStatus.UNKNOWN,
                "status_description": f"No tracker for {package.carrier}",
                "events": []
            }

        return await tracker.track(package.tracking_number)

    async def update_package_status(self, db, package: Package) -> Package:
        """Update package status from carrier API."""
        result = await self.track_package(package)

        # Update package
        package.status = result.get("status", PackageStatus.UNKNOWN)
        package.status_description = result.get("status_description", "")
        package.current_location = result.get("current_location", "")
        package.estimated_delivery = result.get("estimated_delivery")
        package.last_checked = datetime.utcnow()

        if result.get("status") == PackageStatus.DELIVERED:
            package.actual_delivery = datetime.utcnow()

        # Add new tracking events
        existing_events = {(e.timestamp, e.status) for e in package.tracking_history}

        for event_data in result.get("events", []):
            event_key = (event_data["timestamp"], event_data["status"])
            if event_key not in existing_events:
                event = TrackingEvent(
                    package_id=package.id,
                    timestamp=event_data["timestamp"],
                    status=event_data["status"],
                    description=event_data.get("description", ""),
                    location=event_data.get("location", "")
                )
                db.add(event)

        db.commit()
        db.refresh(package)

        return package
```

### 4. Email Parsing Service

#### backend/app/services/email_parser.py:
```python
import re
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from app.models.package import CarrierType
from app.services.carrier_detection import CarrierDetector


@dataclass
class ParsedPackage:
    tracking_number: str
    carrier: CarrierType
    description: Optional[str]
    email_subject: str
    email_date: datetime


class EmailParser:
    """Parse shipping notification emails for tracking numbers."""

    # Email subject patterns that indicate shipping notifications
    SHIPPING_SUBJECTS = [
        r'shipped',
        r'tracking',
        r'on its way',
        r'out for delivery',
        r'delivery',
        r'your order',
        r'package',
        r'shipment',
    ]

    # Sender patterns for major retailers/carriers
    KNOWN_SENDERS = {
        'usps.com': CarrierType.USPS,
        'ups.com': CarrierType.UPS,
        'fedex.com': CarrierType.FEDEX,
        'amazon.com': CarrierType.AMAZON,
    }

    # Tracking number extraction patterns
    TRACKING_PATTERNS = [
        # USPS
        (r'\b(9[0-9]{21,27})\b', CarrierType.USPS),
        (r'\b([0-9]{20,22})\b', CarrierType.USPS),

        # UPS
        (r'\b(1Z[A-Z0-9]{16})\b', CarrierType.UPS),

        # FedEx
        (r'\b([0-9]{12})\b', CarrierType.FEDEX),
        (r'\b([0-9]{15})\b', CarrierType.FEDEX),

        # Amazon
        (r'\b(TBA[0-9]{12,})\b', CarrierType.AMAZON),
    ]

    def parse_email_body(self, body: str, subject: str = "") -> List[ParsedPackage]:
        """Extract tracking numbers from email body."""
        packages = []
        found_numbers = set()

        # Clean body text
        clean_body = body.upper()

        for pattern, suggested_carrier in self.TRACKING_PATTERNS:
            matches = re.findall(pattern, clean_body)
            for match in matches:
                if match not in found_numbers:
                    # Verify with carrier detector
                    detected_carrier, confidence = CarrierDetector.detect(match)

                    if confidence > 0.5:
                        found_numbers.add(match)
                        packages.append(ParsedPackage(
                            tracking_number=match,
                            carrier=detected_carrier,
                            description=self._extract_description(body, match),
                            email_subject=subject,
                            email_date=datetime.utcnow()
                        ))

        return packages

    def _extract_description(self, body: str, tracking_number: str) -> Optional[str]:
        """Try to extract item description near tracking number."""
        # Look for common patterns like "Item: Product Name"
        patterns = [
            r'item[:\s]+([^\n]{5,50})',
            r'product[:\s]+([^\n]{5,50})',
            r'order[:\s]+([^\n]{5,50})',
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:100]

        return None

    def is_shipping_email(self, subject: str, sender: str) -> bool:
        """Check if email is likely a shipping notification."""
        subject_lower = subject.lower()
        sender_lower = sender.lower()

        # Check sender domain
        for domain in self.KNOWN_SENDERS:
            if domain in sender_lower:
                return True

        # Check subject
        for pattern in self.SHIPPING_SUBJECTS:
            if re.search(pattern, subject_lower):
                return True

        return False


class IMAPEmailFetcher:
    """Fetch emails via IMAP."""

    def __init__(self, server: str, port: int, email_address: str, password: str):
        self.server = server
        self.port = port
        self.email_address = email_address
        self.password = password
        self.parser = EmailParser()

    def fetch_shipping_emails(self, since_days: int = 7) -> List[ParsedPackage]:
        """Fetch and parse shipping emails from the last N days."""
        packages = []

        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.server, self.port)
            mail.login(self.email_address, self.password)
            mail.select("INBOX")

            # Search for recent emails
            since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
            _, message_numbers = mail.search(None, f'(SINCE "{since_date}")')

            for num in message_numbers[0].split():
                _, msg_data = mail.fetch(num, "(RFC822)")

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        # Get subject and sender
                        subject = self._decode_header(msg["Subject"])
                        sender = self._decode_header(msg["From"])

                        # Check if shipping email
                        if self.parser.is_shipping_email(subject, sender):
                            body = self._get_email_body(msg)
                            found = self.parser.parse_email_body(body, subject)
                            packages.extend(found)

            mail.logout()

        except Exception as e:
            print(f"Error fetching emails: {e}")

        return packages

    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if header is None:
            return ""

        decoded_parts = decode_header(header)
        result = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result += part.decode(encoding or "utf-8", errors="ignore")
            else:
                result += part
        return result

    def _get_email_body(self, msg) -> str:
        """Extract email body text."""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        pass
                elif content_type == "text/html" and not body:
                    try:
                        html = part.get_payload(decode=True).decode()
                        # Strip HTML tags for simple parsing
                        body = re.sub(r'<[^>]+>', ' ', html)
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                pass

        return body
```

### 5. API Endpoints

#### backend/app/api/v1/packages.py:
```python
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.package import Package, TrackingEvent, CarrierType, PackageStatus
from app.schemas.package import (
    PackageCreate, PackageUpdate, PackageResponse, 
    PackageListResponse, TrackingEventResponse
)
from app.api.deps import get_current_user
from app.services.carrier_detection import CarrierDetector
from app.services.tracking_service import TrackingService

router = APIRouter(prefix="/packages", tags=["packages"])
tracking_service = TrackingService()


@router.get("", response_model=PackageListResponse)
async def list_packages(
    include_archived: bool = False,
    status: Optional[PackageStatus] = None,
    carrier: Optional[CarrierType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all packages for the current user."""
    query = db.query(Package).filter(Package.user_id == current_user.id)

    if not include_archived:
        query = query.filter(Package.is_archived == False)

    if status:
        query = query.filter(Package.status == status)

    if carrier:
        query = query.filter(Package.carrier == carrier)

    packages = query.order_by(Package.created_at.desc()).all()

    return {
        "packages": packages,
        "total": len(packages),
        "active": sum(1 for p in packages if p.status not in [PackageStatus.DELIVERED])
    }


@router.post("", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    package_data: PackageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new package to track."""
    # Clean tracking number
    tracking_number = package_data.tracking_number.upper().replace(" ", "").replace("-", "")

    # Check for duplicate
    existing = db.query(Package).filter(
        Package.user_id == current_user.id,
        Package.tracking_number == tracking_number,
        Package.is_archived == False
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Package with this tracking number already exists"
        )

    # Detect carrier if not provided
    if package_data.carrier:
        carrier = package_data.carrier
    else:
        carrier, confidence = CarrierDetector.detect(tracking_number)

    # Create package
    package = Package(
        user_id=current_user.id,
        tracking_number=tracking_number,
        carrier=carrier,
        description=package_data.description,
        source="manual"
    )

    db.add(package)
    db.commit()
    db.refresh(package)

    # Queue background status check
    background_tasks.add_task(update_package_status_task, db, package.id)

    return package


@router.get("/{package_id}", response_model=PackageResponse)
async def get_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get package details with tracking history."""
    package = db.query(Package).filter(
        Package.id == package_id,
        Package.user_id == current_user.id
    ).first()

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    return package


@router.put("/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: int,
    package_data: PackageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update package details."""
    package = db.query(Package).filter(
        Package.id == package_id,
        Package.user_id == current_user.id
    ).first()

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # Update fields
    if package_data.description is not None:
        package.description = package_data.description
    if package_data.carrier is not None:
        package.carrier = package_data.carrier
    if package_data.is_archived is not None:
        package.is_archived = package_data.is_archived

    db.commit()
    db.refresh(package)

    return package


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a package."""
    package = db.query(Package).filter(
        Package.id == package_id,
        Package.user_id == current_user.id
    ).first()

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # Delete tracking events first
    db.query(TrackingEvent).filter(TrackingEvent.package_id == package_id).delete()
    db.delete(package)
    db.commit()


@router.post("/{package_id}/refresh", response_model=PackageResponse)
async def refresh_package_status(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually refresh package status from carrier."""
    package = db.query(Package).filter(
        Package.id == package_id,
        Package.user_id == current_user.id
    ).first()

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # Update status
    package = await tracking_service.update_package_status(db, package)

    return package


@router.post("/{package_id}/archive", response_model=PackageResponse)
async def archive_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a delivered package."""
    package = db.query(Package).filter(
        Package.id == package_id,
        Package.user_id == current_user.id
    ).first()

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    package.is_archived = True
    db.commit()
    db.refresh(package)

    return package


@router.post("/detect-carrier")
async def detect_carrier(
    tracking_number: str,
    current_user: User = Depends(get_current_user)
):
    """Detect carrier from tracking number."""
    carrier, confidence = CarrierDetector.detect(tracking_number)

    return {
        "tracking_number": tracking_number,
        "carrier": carrier,
        "confidence": confidence
    }


# Background task
async def update_package_status_task(db: Session, package_id: int):
    """Background task to update package status."""
    package = db.query(Package).filter(Package.id == package_id).first()
    if package:
        await tracking_service.update_package_status(db, package)
```

### 6. Pydantic Schemas

#### backend/app/schemas/package.py:
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.package import CarrierType, PackageStatus


class PackageCreate(BaseModel):
    tracking_number: str = Field(..., min_length=8, max_length=100)
    carrier: Optional[CarrierType] = None
    description: Optional[str] = Field(None, max_length=255)


class PackageUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    carrier: Optional[CarrierType] = None
    is_archived: Optional[bool] = None


class TrackingEventResponse(BaseModel):
    id: int
    timestamp: datetime
    status: str
    description: Optional[str]
    location: Optional[str]

    class Config:
        from_attributes = True


class PackageResponse(BaseModel):
    id: int
    tracking_number: str
    carrier: CarrierType
    description: Optional[str]
    status: PackageStatus
    status_description: Optional[str]
    current_location: Optional[str]
    estimated_delivery: Optional[datetime]
    actual_delivery: Optional[datetime]
    source: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    last_checked: Optional[datetime]
    tracking_history: List[TrackingEventResponse] = []

    class Config:
        from_attributes = True


class PackageListResponse(BaseModel):
    packages: List[PackageResponse]
    total: int
    active: int
```

### 7. Frontend Widget Component

#### frontend/src/components/widgets/PackageTrackingWidget.jsx:
```jsx
import React, { useState, useEffect } from 'react';
import { 
  Package, Plus, RefreshCw, Archive, Trash2, 
  Truck, CheckCircle, AlertCircle, Clock 
} from 'lucide-react';
import { usePackages } from '../../hooks/usePackages';

const STATUS_CONFIG = {
  pending: { icon: Clock, color: 'text-gray-500', bg: 'bg-gray-100' },
  pre_transit: { icon: Package, color: 'text-blue-500', bg: 'bg-blue-100' },
  in_transit: { icon: Truck, color: 'text-yellow-500', bg: 'bg-yellow-100' },
  out_for_delivery: { icon: Truck, color: 'text-green-500', bg: 'bg-green-100' },
  delivered: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100' },
  exception: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-100' },
  unknown: { icon: Clock, color: 'text-gray-400', bg: 'bg-gray-100' },
};

const CARRIER_LOGOS = {
  usps: '📬',
  ups: '📦',
  fedex: '📫',
  amazon: '📦',
  other: '📦',
};

export default function PackageTrackingWidget({ config }) {
  const { 
    packages, 
    loading, 
    addPackage, 
    refreshPackage, 
    archivePackage,
    deletePackage 
  } = usePackages();

  const [showAddForm, setShowAddForm] = useState(false);
  const [newTracking, setNewTracking] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [selectedPackage, setSelectedPackage] = useState(null);

  const activePackages = packages.filter(p => !p.is_archived);

  const handleAddPackage = async (e) => {
    e.preventDefault();
    if (!newTracking.trim()) return;

    await addPackage({
      tracking_number: newTracking,
      description: newDescription || null
    });

    setNewTracking('');
    setNewDescription('');
    setShowAddForm(false);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5" />
          <h3 className="font-semibold">Package Tracking</h3>
          <span className="text-sm text-gray-500">
            ({activePackages.length} active)
          </span>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>

      {/* Add Package Form */}
      {showAddForm && (
        <form onSubmit={handleAddPackage} className="mb-4 p-3 bg-gray-50 rounded-lg">
          <input
            type="text"
            placeholder="Tracking number"
            value={newTracking}
            onChange={(e) => setNewTracking(e.target.value)}
            className="w-full p-2 border rounded mb-2"
            autoFocus
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            className="w-full p-2 border rounded mb-2"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
            >
              Add Package
            </button>
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 border rounded hover:bg-gray-100"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Package List */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : activePackages.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Package className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No packages being tracked</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="mt-2 text-blue-500 hover:underline"
            >
              Add a package
            </button>
          </div>
        ) : (
          activePackages.map((pkg) => {
            const statusConfig = STATUS_CONFIG[pkg.status] || STATUS_CONFIG.unknown;
            const StatusIcon = statusConfig.icon;

            return (
              <div
                key={pkg.id}
                className="p-3 border rounded-lg hover:shadow-sm cursor-pointer"
                onClick={() => setSelectedPackage(pkg)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{CARRIER_LOGOS[pkg.carrier]}</span>
                    <div>
                      <p className="font-medium text-sm">
                        {pkg.description || pkg.tracking_number}
                      </p>
                      <p className="text-xs text-gray-500 font-mono">
                        {pkg.tracking_number}
                      </p>
                    </div>
                  </div>
                  <div className={`flex items-center gap-1 px-2 py-1 rounded ${statusConfig.bg}`}>
                    <StatusIcon className={`w-3 h-3 ${statusConfig.color}`} />
                    <span className={`text-xs capitalize ${statusConfig.color}`}>
                      {pkg.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>

                {pkg.estimated_delivery && pkg.status !== 'delivered' && (
                  <p className="text-xs text-gray-500 mt-2">
                    Est. delivery: {formatDate(pkg.estimated_delivery)}
                  </p>
                )}

                {pkg.status === 'delivered' && pkg.actual_delivery && (
                  <p className="text-xs text-green-600 mt-2">
                    Delivered: {formatDate(pkg.actual_delivery)}
                  </p>
                )}

                {/* Quick Actions */}
                <div className="flex gap-2 mt-2 pt-2 border-t">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      refreshPackage(pkg.id);
                    }}
                    className="text-xs text-gray-500 hover:text-blue-500 flex items-center gap-1"
                  >
                    <RefreshCw className="w-3 h-3" /> Refresh
                  </button>
                  {pkg.status === 'delivered' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        archivePackage(pkg.id);
                      }}
                      className="text-xs text-gray-500 hover:text-green-500 flex items-center gap-1"
                    >
                      <Archive className="w-3 h-3" /> Archive
                    </button>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('Delete this package?')) {
                        deletePackage(pkg.id);
                      }
                    }}
                    className="text-xs text-gray-500 hover:text-red-500 flex items-center gap-1"
                  >
                    <Trash2 className="w-3 h-3" /> Delete
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Package Detail Modal */}
      {selectedPackage && (
        <PackageDetailModal
          package={selectedPackage}
          onClose={() => setSelectedPackage(null)}
        />
      )}
    </div>
  );
}

function PackageDetailModal({ package: pkg, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-semibold text-lg">
              {pkg.description || 'Package Details'}
            </h3>
            <p className="text-sm text-gray-500 font-mono">{pkg.tracking_number}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Carrier</p>
              <p className="font-medium capitalize">{pkg.carrier}</p>
            </div>
            <div>
              <p className="text-gray-500">Status</p>
              <p className="font-medium capitalize">{pkg.status.replace('_', ' ')}</p>
            </div>
          </div>

          {pkg.status_description && (
            <div className="text-sm">
              <p className="text-gray-500">Latest Update</p>
              <p>{pkg.status_description}</p>
            </div>
          )}

          {/* Tracking History */}
          {pkg.tracking_history && pkg.tracking_history.length > 0 && (
            <div>
              <p className="text-sm text-gray-500 mb-2">Tracking History</p>
              <div className="space-y-2">
                {pkg.tracking_history.map((event, idx) => (
                  <div key={idx} className="text-sm border-l-2 border-gray-200 pl-3">
                    <p className="font-medium">{event.status}</p>
                    {event.location && (
                      <p className="text-gray-500">{event.location}</p>
                    )}
                    <p className="text-xs text-gray-400">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

### 8. React Hook

#### frontend/src/hooks/usePackages.js:
```javascript
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export function usePackages() {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPackages = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/packages');
      setPackages(response.data.packages);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPackages();
  }, [fetchPackages]);

  const addPackage = async (packageData) => {
    try {
      const response = await api.post('/packages', packageData);
      setPackages(prev => [response.data, ...prev]);
      return response.data;
    } catch (err) {
      throw err;
    }
  };

  const refreshPackage = async (packageId) => {
    try {
      const response = await api.post(`/packages/${packageId}/refresh`);
      setPackages(prev => 
        prev.map(p => p.id === packageId ? response.data : p)
      );
      return response.data;
    } catch (err) {
      throw err;
    }
  };

  const archivePackage = async (packageId) => {
    try {
      await api.post(`/packages/${packageId}/archive`);
      setPackages(prev => prev.filter(p => p.id !== packageId));
    } catch (err) {
      throw err;
    }
  };

  const deletePackage = async (packageId) => {
    try {
      await api.delete(`/packages/${packageId}`);
      setPackages(prev => prev.filter(p => p.id !== packageId));
    } catch (err) {
      throw err;
    }
  };

  return {
    packages,
    loading,
    error,
    fetchPackages,
    addPackage,
    refreshPackage,
    archivePackage,
    deletePackage
  };
}
```

## Unit Tests

### tests/test_carrier_detection.py:
```python
import pytest
from app.services.carrier_detection import CarrierDetector
from app.models.package import CarrierType

def test_detect_usps_tracking():
    # 22-digit USPS
    carrier, conf = CarrierDetector.detect("9400111899223033005282")
    assert carrier == CarrierType.USPS
    assert conf > 0.5

def test_detect_ups_tracking():
    carrier, conf = CarrierDetector.detect("1Z999AA10123456784")
    assert carrier == CarrierType.UPS
    assert conf > 0.8

def test_detect_fedex_tracking():
    # 12-digit FedEx
    carrier, conf = CarrierDetector.detect("123456789012")
    assert carrier == CarrierType.FEDEX
    assert conf > 0.5

def test_detect_amazon_tracking():
    carrier, conf = CarrierDetector.detect("TBA123456789012")
    assert carrier == CarrierType.AMAZON
    assert conf > 0.8

def test_detect_unknown():
    carrier, conf = CarrierDetector.detect("ABC123")
    assert carrier == CarrierType.OTHER
    assert conf == 0.0

def test_handles_spaces_and_dashes():
    carrier, conf = CarrierDetector.detect("1Z 999-AA1-0123-4567-84")
    assert carrier == CarrierType.UPS
```

## Acceptance Criteria
- [ ] Manual package entry works with auto carrier detection
- [ ] Package list displays with status icons
- [ ] Package detail view shows tracking history
- [ ] Refresh updates status from carrier API
- [ ] Archive moves delivered packages out of active list
- [ ] Delete removes package completely
- [ ] Email parsing extracts tracking numbers (when configured)
- [ ] Carrier detection works for USPS, UPS, FedEx, Amazon
- [ ] Unit tests pass

## Notes
- USPS API is free but requires registration
- UPS/FedEx APIs may require paid accounts for full access
- Amazon tracking relies primarily on email parsing
- Consider adding AfterShip API as fallback for better coverage

## Estimated Time
4-5 hours

## Next Task
Task 012: Weather Widget
