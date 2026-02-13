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
    email_sender: str  # Full sender string (e.g., "Amazon.com <order@amazon.com>")
    email_body_snippet: str  # First 1000 chars of email body
    tracking_url: Optional[str] = None  # Actual tracking URL from email


class DeliveryConfirmation(BaseModel):
    tracking_number: str
    carrier: str
    delivered_date: str  # ISO datetime from email
    found_in_subject: str
    found_in_email: str
    email_sender: str
    email_body_snippet: str
    tracking_url: Optional[str] = None


class EmailScanResponse(BaseModel):
    tracking_numbers: list[TrackingNumber]
    delivery_confirmations: list[DeliveryConfirmation]
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
        r'\b(TBA\d{9})\b',   # TBA followed by 9 digits (Amazon Logistics)
        r'\b(TBA[A-Z0-9]{10,12})\b',  # TBA with alphanumeric
        r'\b([A-Z]{2}\d{12,15}[A-Z]{2})\b',  # Amazon International format
        r'\b(AMA[A-Z0-9]{9,12})\b',  # AMA prefix format
    ],
}


def extract_tracking_numbers(text: str) -> list[tuple[str, str]]:
    """Extract tracking numbers from text. Returns list of (number, carrier) tuples."""
    found = []
    seen = set()

    # Convert to uppercase for matching
    text_upper = text.upper()

    # Extract Amazon order/shipment IDs from tracking URLs
    # Amazon often doesn't show tracking numbers, only order IDs in URLs
    amazon_url_pattern = r'amazon\.com/(?:progress-tracker/package|gp/css/shiptrack/view\.html)[^\s]*?(?:orderId|orderID)=([0-9\-]+)'
    amazon_matches = re.finditer(amazon_url_pattern, text, re.IGNORECASE)
    for match in amazon_matches:
        order_id = match.group(1)
        # Use order ID as tracking identifier for Amazon
        if order_id not in seen:
            seen.add(order_id)
            found.append((order_id, 'Amazon'))

    # Try each carrier's patterns
    for carrier, patterns in TRACKING_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text_upper)
            for match in matches:
                tracking = match.group(1)
                if tracking not in seen:
                    seen.add(tracking)
                    found.append((tracking, carrier))

    # Additional heuristic: look for common tracking number formats after keywords
    # This catches numbers that might not match strict patterns
    tracking_keywords = r'(?:tracking|track|shipment|package)\s*(?:number|#|id)?[:\s]+([A-Z0-9\-]{8,30})'
    keyword_matches = re.finditer(tracking_keywords, text_upper, re.IGNORECASE)
    for match in keyword_matches:
        potential_tracking = match.group(1).strip()
        # Remove common separators
        potential_tracking = potential_tracking.replace('-', '').replace(' ', '')
        if len(potential_tracking) >= 8 and potential_tracking not in seen:
            # Try to guess carrier based on format
            carrier = 'other'
            if potential_tracking.startswith('1Z'):
                carrier = 'UPS'
            elif potential_tracking.startswith('TBA'):
                carrier = 'Amazon'
            elif potential_tracking.startswith(('94', '92', '93', '82')):
                carrier = 'USPS'
            elif potential_tracking.isdigit() and len(potential_tracking) in [12, 15, 20]:
                carrier = 'FedEx'

            if potential_tracking not in seen:
                seen.add(potential_tracking)
                found.append((potential_tracking, carrier))

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
    html_body = ""

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
            # Also get HTML if no plain text found
            elif content_type == "text/html" and "attachment" not in content_disposition and not body:
                try:
                    html_body = part.get_payload(decode=True).decode(errors='ignore')
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode(errors='ignore')
        except:
            pass

    # If no plain text found, use HTML (will have tags but tracking numbers should still be extractable)
    if not body and html_body:
        body = html_body

    return body


def is_delivery_confirmation(subject: str, body: str, sender: str) -> bool:
    """
    Determine if an email is a delivery confirmation.
    Checks subject line and body for delivery keywords.
    """
    text_to_check = f"{subject} {body}".lower()

    # Delivery confirmation patterns
    delivery_patterns = [
        'delivered:',  # Amazon style: "Delivered: Package Name"
        'was delivered',
        'has been delivered',
        'delivery complete',
        'successfully delivered',
        'package delivered',
        'your delivery',
        'delivered to',
        'left at',
        'handed directly to resident',
    ]

    # Check if any delivery pattern matches
    return any(pattern in text_to_check for pattern in delivery_patterns)


def clean_email_subject(subject: str) -> str:
    """
    Clean up email subject by removing spam prefixes and common email artifacts.
    """
    if not subject:
        return subject

    # Remove common spam/email prefixes (case-insensitive)
    prefixes_to_remove = [
        r'\*\*\*SPAM\*\*\*\s*',  # ***SPAM***
        r'\[SPAM\]\s*',           # [SPAM]
        r'SPAM:\s*',              # SPAM:
        r'\*\*SPAM\*\*\s*',       # **SPAM**
        r'Re:\s*',                # Re:
        r'Fwd:\s*',               # Fwd:
        r'FW:\s*',                # FW:
    ]

    cleaned = subject
    for prefix_pattern in prefixes_to_remove:
        cleaned = re.sub(prefix_pattern, '', cleaned, flags=re.IGNORECASE)

    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()

    return cleaned


def extract_tracking_url(body: str, carrier: str) -> Optional[str]:
    """
    Extract tracking URL from email body based on carrier.
    Returns the first valid tracking URL found, or None.
    """
    if not body:
        return None

    # Define URL patterns for each carrier
    url_patterns = {
        'Amazon': [
            r'https://www\.amazon\.com/progress-tracker/package[^\s<>"]+',
            r'https://www\.amazon\.com/gp/css/shiptrack/[^\s<>"]+',
        ],
        'USPS': [
            r'https://tools\.usps\.com/go/TrackConfirmAction[^\s<>"]+',
            r'https://www\.usps\.com/track[^\s<>"]+',
        ],
        'UPS': [
            r'https://www\.ups\.com/track[^\s<>"]+',
            r'https://wwwapps\.ups\.com/tracking/tracking\.cgi[^\s<>"]+',
        ],
        'FedEx': [
            r'https://www\.fedex\.com/fedextrack[^\s<>"]+',
            r'https://www\.fedex\.com/apps/fedextrack[^\s<>"]+',
        ],
        'DHL': [
            r'https://www\.dhl\.com/[^\s<>"]*tracking[^\s<>"]+',
        ],
    }

    # Get patterns for this carrier
    patterns = url_patterns.get(carrier, [])

    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            url = match.group(0)
            # Clean up any trailing characters that might have been captured
            url = url.rstrip('.,;:')
            return url

    return None


async def scan_imap_email(
    imap_server: str,
    imap_port: int,
    email_address: str,
    password: str,
    days_back: int = 30,
) -> EmailScanResponse:
    """Scan IMAP email for tracking numbers and delivery confirmations."""

    tracking_numbers = []
    delivery_confirmations = []
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
            # Use broader search to catch all possible shipping emails
            search_criteria = [
                'OR',
                ['OR',
                    ['OR', ['FROM', 'amazon'], ['FROM', 'shopify']],
                    ['OR', ['FROM', 'ups'], ['FROM', 'fedex']]
                ],
                ['OR',
                    ['OR', ['FROM', 'usps'], ['FROM', 'dhl']],
                    ['OR', ['SUBJECT', 'tracking'], ['SUBJECT', 'shipped']]
                ],
            ]

            # Also search by date
            search_criteria = ['SINCE', since_date.date(), search_criteria]

            try:
                messages = client.search(search_criteria)
            except:
                # Fallback to simpler search if complex search fails
                # Just get all recent emails and filter in Python
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

                    # Check if this is a delivery confirmation
                    is_delivered = is_delivery_confirmation(subject, body, sender)

                    # Debug logging
                    if 'amazon' in sender.lower() or 'amazon' in subject.lower():
                        print(f"DEBUG: Amazon email found")
                        print(f"  Sender: {sender}")
                        print(f"  Subject: {subject}")
                        print(f"  Body preview: {body[:500]}")
                        print(f"  Tracking numbers found: {found}")
                        print(f"  Is delivery confirmation: {is_delivered}")

                    # Process found tracking numbers
                    for tracking, carrier in found:
                        # Try to extract tracking URL from email body
                        tracking_url = extract_tracking_url(body, carrier)

                        if is_delivered:
                            # Add to delivery confirmations
                            delivery_confirmations.append(DeliveryConfirmation(
                                tracking_number=tracking,
                                carrier=carrier,
                                delivered_date=date_str or datetime.now().isoformat(),
                                found_in_subject=subject[:100],
                                found_in_email=sender,
                                email_sender=sender,
                                email_body_snippet=body[:1000],
                                tracking_url=tracking_url,
                            ))
                        else:
                            # Add to new shipments
                            tracking_numbers.append(TrackingNumber(
                                tracking_number=tracking,
                                carrier=carrier,
                                found_in_subject=subject[:100],
                                found_in_email=sender,
                                found_date=datetime.now().isoformat(),
                                email_sender=sender,
                                email_body_snippet=body[:1000],
                                tracking_url=tracking_url,
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
        delivery_confirmations=delivery_confirmations,
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
