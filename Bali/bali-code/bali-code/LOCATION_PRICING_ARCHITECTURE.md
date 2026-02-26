# Location Zones & Dynamic Pricing Strategy

## Overview

To provide flexible, zone-based pricing structures for varying regions in Bali (e.g., Zone 1, Zone 2, Ubud, Canggu), the backend booking and payment infrastructure now dynamically resolves the physical scan location of the user and queries the correct markup strategy from the administrative Google Sheets dataset.

## Flow Execution

1. **QR -> Location Verification (`menu_services.py`)**
   - The user scans a QR code that drives them to WhatsApp (`"Hi, I am in {Villa Name}"`).
   - The system queries `cache["villas_data"]` (fed by the `QR Codes` sheet).
   - The exact `Location` (Zone) string is extracted based on the `villa_code`.

2. **Booking Invoice Generation (`payment_service.py`)**
   - `create_xendit_payment_with_distribution()` resolves the user's `order.villa_code` into a `location_zone`.
   - This `location_zone` is actively injected as a parameter into the `/price_distribution` data fetch operation.

3. **Dynamic Markup Resolution (`main_menu_routes.py`)**
   - The system checks the `Mark-up` sheet for a column string exactly matching the `location_zone` (e.g. `Zone 1`).
   - **Match**: The specific zone commission limit is automatically pulled, dictating the `villa_price`.
   - **Fallback**: If the specific column does not exist or is empty (e.g., `"nan"`), it defaults securely to the base `Villa Comm` baseline column to prevent mathematical division errors.

## Xendit Integrations

- As the dynamic `villa_price` and static `vendor_price` are accurately extracted from the zone queries, the `InvoiceApi` automatically configures the appropriate financial splits asynchronously via Xendit rules. No manual adjustments or re-deployments are necessary when new zone rates are published to the Google Sheet.
