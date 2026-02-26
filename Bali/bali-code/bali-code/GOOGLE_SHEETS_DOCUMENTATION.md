# EASYBali Google Sheets Structure

## Master Spreadsheet (ID: `1tuGBnQFjDntJQglofA17uHhiyekkVyDoSInErbwfR24`)

This spreadsheet serves as the central brain for the EASYBali system, controlling everything from UI design to pricing and AI context.

### 1. Menu Structure

- **Columns**: `Main Menu`, `Category`, `Sub-category`.
- **Purpose**: Defines the navigation hierarchy of the chatbot and the web app.

### 2. Services Overview

- **Columns**: `Sub-category`, `Service Item`, `Service Item Description`, `Image URL`, `Final Price (Service Item Button)`, `Service Provider Number`.
- **Purpose**: The direct source of truth for all bookable services.

### 3. Mark-up

- **Columns**: `Service Item`, `Vendor Price`, `Villa Comm`, `Seminyak`, `Ubud`, `Canggu`, `Zone 1`, `Zone 2`.
- **Purpose**: controls the dynamic pricing logic. If a `location_zone` matches a column header, that specific markup is used. Otherwise, it falls back to `Villa Comm`.

### 4. Services Providers

- **Columns**: `Number`, `Name`, `WhatsApp`, `Bank`, `Account Number`, `Swift Code`.
- **Purpose**: Storage of provider contact and bank details for automated xendit disbursements.

### 5. QR Codes (Villa Data)

- **Columns**: `Number` (Villa Code), `Name of Villa`, `Address`, `Location` (Zone), `Bank`, `Account Number`.
- **Purpose**: Maps QR codes to villas and identifies the `location_zone` for pricing.

### 6. AI Data (RAG Source)

- **Columns**: `Service Item`, `Service Item Description`, `Long Description`, `Cultural Context`.
- **Purpose**: Used for real-time RAG context when the user asks questions that aren't direct booking requests.

### 7. Menu Design & Services Designs

- **Purpose**: controls the UI look and feel, including component titles, descriptions, and pictures shown in the web app.

---
**Maintenance Note**: Always ensure that names (Villa Names, Service Items) are consistent across all sheets to avoid lookup failures.
