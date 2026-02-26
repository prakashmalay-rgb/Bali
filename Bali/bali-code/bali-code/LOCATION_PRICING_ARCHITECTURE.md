# Location-Based Pricing Architecture

## Overview

EASYBali implements dynamic pricing based on the geographical zone of the villa. This allows for zone-specific markups and split payment distributions.

## Zone Identification

- Each villa has a `location_zone` attribute defined in the "QR Codes" sheet.
- Supported Zones: `Seminyak`, `Ubud`, `Canggu`, `Zone 1`, `Zone 2`.
- When a guest starts a session, their `villa_code` is used to look up the corresponding zone.

## Pricing Logic

1. **Lookup**: The system queries the "Mark-up" sheet for the requested `service_item`.
2. **Base Price**: Fetched from the `Vendor Price` column.
3. **Markup Selection**:
    - If a column matching the guest's `location_zone` exists and has a value, that value is used as the villa commission.
    - Otherwise, it falls back to the default `Villa Comm` column.
4. **Final Price**: `Total = Vendor Price + Villa Commission`.

## Split Payments (Xendit)

- The calculated distribution is stored in the order object:
  - **Service Provider Share**: `Vendor Price`.
  - **Villa Share**: `Villa Commission`.
- Upon successful payment, Xendit disbursements are triggered to the respective bank accounts of the Provider and the Villa Manager.

## Testing & Validation

- Use the `test_pricing.cjs` script to simulate different zones.
- Ensure the columns in the "Mark-up" sheet exactly match the zone names used in the "QR Codes" sheet.
