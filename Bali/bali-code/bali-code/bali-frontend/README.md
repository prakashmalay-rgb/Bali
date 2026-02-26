# EASY-BALI Frontend

A high-performance, accessible **React + Vite** web application for the EASY-BALI Guest Concierge and Villa Admin Dashboard.

---

## ✨ Features

- **Modern UI**: Tailored aesthetics using Vanilla CSS + Tailwind + SCSS.
- **WebP Optimized**: Asset-heavy sections optimized for sub-second loads.
- **Accessibility**: ARIA-standard keyboard navigation and screen-reader support.
- **Real-time AI Chat**: Integrated with the EASY-BALI backend for instant concierge support.
- **Seamless Transitions**: Framer Motion powered page/layout animations.

---

## 🛠 Tech Stack

- **Framework**: React 18 (Vite)
- **Styling**: Tailwind CSS, SCSS (Components), Vanilla CSS
- **Animations**: Framer Motion
- **State/Routing**: React Router 6, Context API
- **Feedback**: React-Toastify, SweetAlert2

---

## 🚀 Development

### 1. Prerequisites

- Node.js 18+
- NPM or PNPM

### 2. Getting Started

```bash
# Install dependencies
npm install

# Run dev server
npm run dev
```

### 3. Environment Variables

Create a `.env` file in the root:

```text
VITE_API_URL=https://your-backend-url.com
VITE_WA_PHONE_NUMBER=your-whatsapp-number
```

---

## 📁 Components & Style

### `src/components/`

- **`chatbot/`**: Core chat logic and UI.
- **`layout/`**: Shared Navbar, Footer, and Page Transitions.
- **`shared/`**: Atomic design components (Buttons, Inputs, Modals).

### `src/style/`

- **`main.scss`**: Global imports.
- **`pages/`**: Page-specific styling (Hero, Services, Experience).
- **`_tokens.scss`**: Design system tokens (Colors, Spacing).

---

## ♿ Accessibility

This project follows WCAG 2.1 guidelines:

- Descriptive `aria-labels` on all interactive elements.
- Semantic HTML (`<nav>`, `<main>`, `<header>`).
- Full focus management for keyboard-only users.

---

## 📦 Deployment

Deploy via **Vercel** or **Netlify**.

- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variables: Ensure `VITE_API_URL` is set in the dashboard.
