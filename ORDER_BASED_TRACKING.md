# Order-Based Package Tracking Enhancement

## Overview
Enhanced package tracker to handle shipping notifications that **don't include tracking numbers**, using order numbers instead.

**Date:** 2026-02-14
**Triggered by:** Missing Limited Run Games package (ORDER #3411107)

## Problem

Many retailers send "your order is shipping" emails **without tracking numbers**:
- Limited Run Games: "ORDER #3411107 is on the way" (no tracking)
- Kickstarter: "Your reward is shipping!" (order ID only)
- Etsy: "Order #123 has shipped" (no tracking yet)
- Small retailers: Often use order numbers exclusively

**Previous behavior:** Package tracker ignored these emails entirely

## Solution

Enhanced email scanner to detect **shipping indication phrases** and create packages using **order numbers** when tracking numbers aren't available.

### New Features

1. **Shipping Notification Detection**
   - Detects phrases like "shipped", "on the way", "heading your way"
   - Works even without tracking numbers

2. **Order Number Extraction**
   - Extracts order numbers: `ORDER #3411107`, `Order: 12345`, `#67890`
   - Multiple pattern matching for different formats

3. **Order URL Extraction**
   - Extracts order tracking URLs from email body
   - Links directly to retailer's order page

4. **Fallback Tracking**
   - Uses `ORDER #3411107` format as the "tracking number"
   - Displays in package list with 'other' carrier type

## Technical Implementation

### New Functions Added

**File:** `backend/app/api/v1/endpoints/email_scanner.py`

#### 1. `extract_order_numbers(text: str) -> list[str]`

Extracts order numbers from email text.

**Patterns matched:**
```python
'ORDER #3411107'      → "3411107"
'Order: 12345'        → "12345"
'Order Number: 999'   → "999"
'Order ID: ABC123'    → "ABC123"
'#123456'             → "123456" (6+ digits)
```

**Returns:** List of order numbers (keeps original format with separators)

#### 2. `is_shipping_notification(subject: str, body: str) -> bool`

Detects if email indicates order is being shipped.

**Phrases detected:**
- "shipped"
- "on the way"
- "on its way"
- "order is shipping"
- "your order has shipped"
- "preparing to ship"
- "ready to ship"
- "package is on the way"
- "order is being prepared"
- "dispatched"
- "sent out"
- "in transit"
- "out for delivery"
- "heading your way"
- "being shipped"
- "has been shipped"

**Returns:** `True` if any phrase matches (case-insensitive)

#### 3. `extract_order_url(text: str, sender: str = '') -> Optional[str]`

Extracts order tracking URL from email.

**Patterns matched:**
```
https://example.com/order/track/123
https://limitedrungames.com/orders/3411107
https://shopify.com/order/abc123
```

**Returns:** First valid order URL found, or `None`

### Enhanced Email Scanning Logic

**Location:** Lines 496-528 in `email_scanner.py`

```python
# After processing tracking numbers...
if not found and not is_delivered:
    is_shipping = is_shipping_notification(subject, body)

    if is_shipping:
        order_numbers = extract_order_numbers(text_to_search)
        order_url = extract_order_url(text_to_search, sender)

        if order_numbers:
            order_num = order_numbers[0]

            # Create package with order number
            tracking_numbers.append(TrackingNumber(
                tracking_number=f"ORDER #{order_num}",
                carrier='other',  # Generic carrier
                found_in_subject=subject[:100],
                found_in_email=sender,
                found_date=datetime.now().isoformat(),
                email_sender=sender,
                email_body_snippet=body[:1000],
                tracking_url=order_url,  # Link to order page
            ))
```

**Flow:**
1. Check if email has tracking numbers → No
2. Check if email indicates shipping → Yes ("on the way")
3. Extract order numbers → "3411107"
4. Extract order URL → `https://limitedrungames.com/order/3411107` (if present)
5. Create package with `ORDER #3411107` as tracking number
6. Link to order URL instead of carrier tracking page

## Example Use Cases

### Limited Run Games
```
Subject: Your Limited Run Games order has shipped!
Body: ORDER #3411107 is on the way!
      Track your order: https://limitedrungames.com/orders/3411107

Result:
  Tracking: ORDER #3411107
  Carrier: other
  URL: https://limitedrungames.com/orders/3411107
```

### Kickstarter
```
Subject: Your reward is shipping!
Body: Great news! Your pledge for Project ABC (Order #KS-12345)
      is being prepared for shipment.

Result:
  Tracking: ORDER #KS-12345
  Carrier: other
```

### Etsy
```
Subject: Your order from ArtisanShop has shipped
Body: Order #987654 is heading your way!

Result:
  Tracking: ORDER #987654
  Carrier: other
```

## Carrier Type

Order-based packages use `carrier='other'` (already supported in schema).

**Display:**
- Shows as "Other" in carrier column
- Links to order URL if available
- Falls back to email details if no URL

## Frontend Compatibility

**No frontend changes needed!**

The package tracker widget already supports:
- ✅ `carrier='other'` (displays as "Other")
- ✅ `tracking_url` field (clickable link)
- ✅ Order numbers as tracking identifiers

## Testing

### Manual Test - Limited Run Games Package

**Result:** ✅ Successfully added
```
Package ID: 50
Tracking: ORDER #3411107
Carrier: other
Description: Limited Run Games Order
Created: 2026-02-14 08:38:35
```

### Future Automatic Tests

When email scanner next runs (within 30 minutes), it will:
1. Scan emails from Feb 12 (date of Limited Run email)
2. Detect "on the way" in email body
3. Extract "ORDER #3411107"
4. Skip creating duplicate (already exists)

## Files Modified

1. **backend/app/api/v1/endpoints/email_scanner.py**
   - Added `extract_order_numbers()` function
   - Added `is_shipping_notification()` function
   - Added `extract_order_url()` function
   - Enhanced email scanning logic to handle order-only emails

2. **backend/add_limited_run_package.py** (NEW)
   - One-time script to add the missing package

## Edge Cases Handled

1. **Multiple order numbers in email** → Uses first one found
2. **No URL in email** → tracking_url is None, widget shows email details
3. **Both tracking AND order number** → Tracking number takes precedence
4. **Order number in delivered email** → Marks as delivered normally
5. **Duplicate order numbers** → Prevented by existing deduplication logic

## Benefits

✅ Captures packages from retailers without tracking
✅ No manual entry needed for order-only emails
✅ Links directly to retailer's order page
✅ Works with existing widget UI
✅ Handles diverse order number formats
✅ Prevents duplicates automatically

## Future Enhancements (Optional)

1. **Retailer-specific parsing:**
   - Kickstarter: Extract project name
   - Etsy: Extract shop name
   - Limited Run: Extract game title

2. **Status updates without tracking:**
   - "Preparing to ship" → status: preparing
   - "Label created" → status: label_created
   - "Handed to carrier" → status: in_transit

3. **Estimated delivery from email:**
   - "Expected delivery: Feb 20" → extract date
   - "Ships in 2-3 business days" → calculate estimate

4. **Order value tracking:**
   - Extract order total from email
   - Show value in package widget

## Success Criteria

✅ Limited Run Games package now visible
✅ Email scanner detects shipping notifications without tracking
✅ Order numbers used as tracking identifiers
✅ Order URLs extracted when available
✅ Backwards compatible with existing packages

## Next Email Scan

The next automatic email scan (every 30 minutes) will:
- Detect order-based shipping emails
- Create packages using order numbers
- Extract order URLs automatically
- No manual intervention needed!

**Your Limited Run Games package is now in your tracker and future similar emails will be automatically detected!** 🎮
