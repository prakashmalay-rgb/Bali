# Booking Flow Architecture

## Overview

The EasyBali backend uses a hybrid stateful session approach coupled with WhatsApp Flows and WebSocket clients to process user bookings smoothly, from service selection down to payment processing. State transitions, payments, automated timeout handlers, and external third-party integrations (Xendit, Meta, Google Sheets) act as critical pillars.

## Core Components

1. **WhatsApp Webhooks & Flow Router (`whatsapp_routes.py`)**:
   - Uses Meta’s end-to-end encrypted Flow JSON API.
   - Initial screening maps user entries to category and service flows.
   - Emits secure AES-encrypted JSON structures allowing WhatsApp UI to dictate state securely without heavy client computation.

2. **Order Summary State Manager (`order_summary.py`)**:
   - Records transient and confirmed session states natively in Motor MongoDB.
   - Logs extensive tracking data allowing granular analytics: order received, pending payment, payment success/failure, recovery initialization.

3. **Payment Service Engine & Distribution (`payment_service.py`)**:
   - Integrates with Xendit via HTTPs requests.
   - Manages automatic pricing splits between Vendor (Service Provider) and Facility (Villa).
   - Generates unified dynamic invoices with built-in robust timeout closures via Retry routines.

4. **Xendit Webhook Monitor (`xendit_webhook.py`)**:
   - Handles real-time asynchronous callbacks (PAID, FAILED, EXPIRED).
   - Engages intelligent recovery workflows upon failed/expired statuses, triggering "Retry" mechanisms via direct WhatsApp messaging.

## Flow Sequences

### 1. Initiation

- **User** initiates a booking command.
- Backend resolves intention via Dialogflow/OpenAI intent logic.
- Returns WhatsApp interactive template with tokenized `action`.

### 2. Form Submission (Data Exchange)

- WhatsApp Client securely decrypts Form UI locally and User inputs selections.
- The `handle_data_exchange` processes inputs, validating minimal thresholds (e.g., minimum booking date, capacity bounds).

### 3. Payment Generation & Orchestration

- Upon submission completion, state transitions to `pending_payment`.
- The webhook pushes invoice links mapped against tracking references directly into chat scope.

### 4. Asynchronous Outcome

- **Success**: Payment webhook resolves -> Disbursement engine activates (funds split to provider/villa) -> Confirmation invoice PDF is served seamlessly.
- **Failures / Timeout**: Exponential backoff/retry handles disbursement exceptions, while Webhook handler proactively resets the interface state and guides user into recovery options.
