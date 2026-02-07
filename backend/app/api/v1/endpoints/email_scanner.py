import re
import email
from datetime import datetime, timedelta
from email.header import decode_header
from imapclient import IMAPClient
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.api.v1.deps import CurrentActiveUser

router = APIRouter(prefix="/email-scanner", tags=["Email Scanner"])


class TrackingNumber(BaseModel):
    tracking_number: str
    carrier: str  # "USPS", "UPS", "FedEx", "Amazon"
    found_in_subject: str
    found_in_email: str  # Email address or sender
    found_date: str  # ISO datetime


class EmailScanResponse(BaseModel):
    tracking_numbers: list[TrackingNumber]
    emails_scanned: int
    scan_date: str


# Tracking number patterns
TRACKING_PATTERNS = {
    "USPS": [
        r'\b(94\d{20})\b',  # 94 followed by 20 digits
        r'\b(92\d{20})\b',  # 92 followed by 20 digits
        r'\b(93\d{20})\b',  # 93 followed by 20 digits
        r'\b(94\d{18})\b',  # 94 followed by 18 digits
        r'\b(82\d{8})\b',   # 82 followed by 8 digits
    ],
    "UPS": [
        r'\b(1Z[A-Z0-9]{16})\b',  # 1Z followed by 16 alphanumeric
    ],
    "FedEx": [
        r'\b(\d{12})\b',  # 12 digits
        r'\b(\d{15})\b',  # 15 digits
        r'\b(\d{20})\b',  # 20 digits (FedEx Ground)
    ],
    "Amazon": [
        r'\b(TBA\d{12})\b',  # TBA followed by 12 digits
        r'\b(TBA\d{10})\b',  # TBA followed by 10 digits
    ],
}


def extract_tracking_numbers(text: str) -> list[tuple[str, str]]:
    """Extract tracking numbers from text. Returns list of (number, carrier) tuples."""
    found = []
    seen = set()

    # Convert to uppercase for matching
    text_upper = text.upper()

    # Try each carrier's patterns
    for carrier, patterns in TRACKING_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text_upper)
            for match in matches:
                tracking = match.group(1)
                if tracking not in seen:
                    seen.add(tracking)
                    found.append((tracking, carrier))

    return found


def decode_email_subject(subject):
    """Decode email subject from encoded format."""
    if not subject:
        return ""

    decoded_parts = []
    for part, encoding in decode_header(subject):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
        else:
            decoded_parts.append(part)
    return ''.join(decoded_parts)


def extract_email_body(msg):
    """Extract plain text body from email message."""
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Get plain text parts
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode(errors='ignore')
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode(errors='ignore')
        except:
            pass

    return body


async def scan_imap_email(
    imap_server: str,
    imap_port: int,
    email_address: str,
    password: str,
    days_back: int = 30,
) -> EmailScanResponse:
    """Scan IMAP email for tracking numbers."""

    tracking_numbers = []
    emails_scanned = 0

    try:
        # Connect to IMAP server
        with IMAPClient(imap_server, port=imap_port, ssl=True) as client:
            # Login
            try:
                client.login(email_address, password)
            except Exception as e:
                raise HTTPException(
                    status_code=401,
                    detail=f"IMAP login failed: {str(e)}. Check your email and password/app password."
                )

            # Select INBOX
            client.select_folder('INBOX', readonly=True)

            # Search for emails from the last N days with shipping-related keywords
            since_date = datetime.now() - timedelta(days=days_back)

            # Search criteria: emails from shipping carriers or with shipping keywords
            search_criteria = [
                'OR',
                ['OR', ['FROM', 'amazon'], ['FROM', 'shopify']],
                ['OR',
                    ['OR', ['FROM', 'ups.com'], ['FROM', 'fedex.com']],
                    ['OR', ['FROM', 'usps.com'], ['SUBJECT', 'tracking']]
                ],
            ]

            # Also search by date
            search_criteria = ['SINCE', since_date.date(), search_criteria]

            try:
                messages = client.search(search_criteria)
            except:
                # Fallback to simpler search if complex search fails
                messages = client.search(['SINCE', since_date.date()])

            # Limit to most recent 100 emails to avoid timeouts
            messages = list(messages)[-100:]

            # Fetch email data
            if messages:
                email_data = client.fetch(messages, ['RFC822'])

                for msg_id, data in email_data.items():
                    emails_scanned += 1

                    # Parse email
                    email_message = email.message_from_bytes(data[b'RFC822'])

                    # Get subject and sender
                    subject = decode_email_subject(email_message.get('Subject', ''))
                    sender = email_message.get('From', '')
                    date_str = email_message.get('Date', '')

                    # Extract body
                    body = extract_email_body(email_message)

                    # Search for tracking numbers in subject and body
                    text_to_search = f"{subject}\n{body}"
                    found = extract_tracking_numbers(text_to_search)

                    for tracking, carrier in found:
                        tracking_numbers.append(TrackingNumber(
                            tracking_number=tracking,
                            carrier=carrier,
                            found_in_subject=subject[:100],  # Truncate
                            found_in_email=sender,
                            found_date=datetime.now().isoformat(),
                        ))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to scan email: {str(e)}"
        )

    return EmailScanResponse(
        tracking_numbers=tracking_numbers,
        emails_scanned=emails_scanned,
        scan_date=datetime.now().isoformat(),
    )


@router.post("/scan", response_model=EmailScanResponse)
async def scan_email_for_tracking(
    current_user: CurrentActiveUser,
    imap_server: str = Query(..., description="IMAP server (e.g., imap.gmail.com)"),
    imap_port: int = Query(993, description="IMAP port (usually 993 for SSL)"),
    email_address: str = Query(..., description="Email address"),
    password: str = Query(..., description="Email password or app password"),
    days_back: int = Query(30, ge=1, le=90, description="Days to scan back"),
):
    """
    Scan IMAP email for package tracking numbers.

    For Gmail:
    - Use imap.gmail.com as server
    - Generate an App Password: myaccount.google.com/apppasswords
    - Use the app password instead of your regular password

    For Outlook/Hotmail:
    - Use outlook.office365.com as server

    For Yahoo:
    - Use imap.mail.yahoo.com as server
    - Generate an App Password in Yahoo account settings
    """

    result = await scan_imap_email(
        imap_server=imap_server,
        imap_port=imap_port,
        email_address=email_address,
        password=password,
        days_back=days_back,
    )

    return result
