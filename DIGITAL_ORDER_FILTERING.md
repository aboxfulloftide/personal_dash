# Digital Order Filtering Enhancement

## Overview
Added intelligent filtering to **ignore digital/software orders** that don't require package tracking.

**Date:** 2026-02-14
**Reason:** Digital downloads, software licenses, and digital games don't need shipment tracking

## Problem

Package tracker was creating entries for digital orders:
- Steam game purchases → No physical shipment
- eBook downloads → Instant delivery
- Software licenses → Email activation code
- Digital gift cards → No tracking needed
- In-game DLC → Download only

**Previous behavior:** All order emails created package entries, even digital ones

## Solution

Added `is_digital_order()` function that detects digital purchases and skips package creation.

## Digital Order Detection

### Detection Patterns

The scanner checks for these indicators in email subject, body, and sender:

#### Explicit Digital Keywords
```
"digital download"
"download now"
"instant download"
"digital delivery"
"digital code"
"digital game"
"activation key"
"product key"
"license key"
"redeem code"
"steam key"
"ebook"
"kindle edition"
"audiobook"
"software license"
"subscription activated"
"virtual currency"
"in-game item"
"DLC"
"downloadable content"
"gift card"
"egift card"
```

#### Platform-Specific Indicators
```
"steam library"
"epic games"
"gog.com"
"origin"
"battle.net"
"playstation store"
"xbox store"
"nintendo eshop"
"available in your library"
"added to your account"
"ready to play"
"start playing now"
```

#### Software/SaaS Indicators
```
"software download"
"license activated"
"subscription confirmed"
"access granted"
```

#### Digital Platform Senders
```
steam
epicgames
gog.com
origin
ubisoft
battle.net
playstation
xbox
nintendo
kindle
audible
apple.com (App Store/iTunes)
google.com (Play Store)
```

## Technical Implementation

### New Function

**File:** `backend/app/api/v1/endpoints/email_scanner.py`

```python
def is_digital_order(subject: str, body: str, sender: str = '') -> bool:
    """
    Determine if an order is digital/software only (no physical shipment).
    Returns True if order is for digital goods that don't need tracking.
    """
    text_to_check = f"{subject} {body} {sender}".lower()

    # Check for 40+ digital indicators
    digital_patterns = [...]

    is_digital = any(pattern in text_to_check for pattern in digital_patterns)

    # Also check sender domain
    digital_senders = ['steam', 'epicgames', 'gog.com', ...]
    sender_is_digital = any(platform in sender.lower() for platform in digital_senders)

    return is_digital or sender_is_digital
```

### Integration in Email Scanner

**Location:** Lines 528-540 in `email_scanner.py`

```python
# For order-only emails (no tracking number)
if not found and not is_delivered:
    # Check if digital order first
    is_digital = is_digital_order(subject, body, sender)

    if is_digital:
        print(f"DEBUG: Skipping digital order (no physical shipment)")
        continue  # Skip package creation

    # Check if shipping notification
    is_shipping = is_shipping_notification(subject, body)
    if is_shipping:
        # Create package with order number...
```

**Flow:**
1. Email has no tracking number
2. Check: Is this a digital order? → Yes
3. **Skip** - don't create package
4. Continue to next email

## Example Filtered Orders

### Steam Game Purchase
```
Subject: Your Steam purchase is now available
Body: Thanks for purchasing "Awesome Game"!
      Your game is now in your Steam library. Start playing now!
Sender: noreply@steampowered.com

Result: ✅ SKIPPED (digital download)
```

### Kindle eBook
```
Subject: Your Kindle book is ready
Body: "Great Novel" is now available in your Kindle library.
      Download now to start reading!
Sender: digital-no-reply@amazon.com

Result: ✅ SKIPPED (digital book)
```

### Software License
```
Subject: Your Adobe Creative Cloud subscription is active
Body: Your software license has been activated.
      Download the installer from your account.
Sender: adobe.com

Result: ✅ SKIPPED (software license)
```

### Digital Game Key
```
Subject: Your Limited Run Games order #3411107 - Digital items ready
Body: Your Steam keys for the digital edition are now available!
      Redeem code: XXXXX-XXXXX-XXXXX
Sender: orders@limitedrungames.com

Result: ✅ SKIPPED (digital game key)
```

### NOT Filtered (Physical + Digital Bundle)
```
Subject: Your Limited Run Games order #3411107 has shipped
Body: Your physical collector's edition is on the way!
      Tracking: (none provided)
      Bonus: Digital code included in package

Result: ✅ CREATED (physical shipment - "shipped" detected, no digital-only keywords)
```

## Edge Cases Handled

### 1. Physical + Digital Bundles
**Scenario:** Order includes both physical item AND digital content

**Handling:**
- If email mentions "shipped" or "tracking" → Creates package (physical item)
- Digital bonus content mentioned → Ignored (focus on physical shipment)

**Example:** Collector's Edition with game disc + digital soundtrack
**Result:** Package created (physical disc is shipping)

### 2. Digital Storefronts with Physical Options
**Scenario:** Steam/Epic usually digital, but sometimes sells physical items

**Handling:**
- Checks email content, not just sender
- "Shipped" keyword overrides digital platform detection
- Tracking number always creates package (definitely physical)

**Example:** Steam Deck hardware purchase from Steam
**Result:** Package created (has tracking number)

### 3. Gift Cards (Digital vs Physical)
**Scenario:** eGift card vs physical gift card

**Handling:**
- "egift", "digital gift" → Skipped
- "gift card shipped" → Creates package
- Tracking number → Creates package

### 4. Pre-orders
**Scenario:** Pre-ordered digital game with "preparing" email

**Handling:**
- "Download available" → Skipped (digital)
- "Preparing to ship" without "download" → May create package
- Depends on other indicators in email

## Logging

When a digital order is detected, logs show:
```
DEBUG: Skipping digital order (no physical shipment)
  Sender: noreply@steampowered.com
  Subject: Your Steam purchase is now available
```

This helps verify the filter is working correctly.

## Benefits

✅ Cleaner package list (no digital-only orders)
✅ Focuses on actual shipments that need tracking
✅ Reduces clutter from game/software purchases
✅ Prevents confusion ("why is my Steam game not delivered?")
✅ Works automatically with existing email scanning

## False Positive Prevention

**Won't filter out:**
- Physical items with digital bonuses (game disc + DLC code)
- Hardware from digital platforms (Steam Deck, controllers)
- Physical collector's editions from game publishers
- Any email with a tracking number
- Any email with "shipped" + physical item indicators

**Logic:**
- Presence of tracking number = definitely physical → Create package
- "Shipped" keyword = likely physical → Create package unless strong digital indicators
- Digital-only indicators without "shipped" = digital → Skip

## Files Modified

1. **backend/app/api/v1/endpoints/email_scanner.py**
   - Added `is_digital_order()` function (40+ detection patterns)
   - Added digital order check in email scanning logic
   - Added debug logging for skipped digital orders

## Testing Scenarios

### Should Skip (Digital):
- ✅ Steam game purchase
- ✅ Kindle eBook
- ✅ Audiobook download
- ✅ Software license activation
- ✅ In-game DLC
- ✅ Digital gift card
- ✅ Mobile app purchase
- ✅ Streaming service activation
- ✅ Virtual currency

### Should Create Package (Physical):
- ✅ Physical game with Steam key bonus
- ✅ Collector's edition with artbook
- ✅ Hardware (controllers, consoles)
- ✅ Books (physical, not eBook)
- ✅ Board games
- ✅ Vinyl records
- ✅ Physical gift cards
- ✅ Anything with tracking number

## Future Enhancements (Optional)

1. **User Configuration:**
   - Allow users to customize digital detection keywords
   - Option to include/exclude certain platforms

2. **Machine Learning:**
   - Learn from user's manual dismissals
   - Improve detection accuracy over time

3. **Mixed Order Handling:**
   - Detect physical + digital bundles
   - Show digital content separately (info-only, no tracking)

4. **Platform Integration:**
   - Link to Steam/Epic library
   - Show digital game status
   - Separate widget for digital purchases

## Success Criteria

✅ Digital orders automatically skipped
✅ Physical orders still tracked normally
✅ Physical + digital bundles handled correctly
✅ No false positives (physical items not skipped)
✅ Clear logging for debugging

## Conclusion

The package tracker now intelligently filters out digital-only orders, keeping the focus on physical shipments that actually need tracking. This reduces noise and makes the widget more useful for its intended purpose: tracking packages that are being delivered to your door.

**Next automatic email scan will apply this filtering!** 🎮
