import React from "react";
import ReactDOM from "react-dom/client";
import { ErrorBoundary } from "react-error-boundary";
import { HelmetProvider } from "react-helmet-async";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import "./style/main.scss";
import "./main.css";
import "sweetalert2/src/sweetalert2.scss";
import AppLayout from "./App.jsx";
import ErrorFallback from "./components/ErrorFallback";

ReactDOM.createRoot(document.getElementById("root")).render(
  <ErrorBoundary
    FallbackComponent={ErrorFallback}
    onReset={() => {
      // Logic to reset state if needed
      window.location.reload();
    }}
  >
    <HelmetProvider>
      <AppLayout />
      <ToastContainer
        position="bottom-right"
        autoClose={4000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </HelmetProvider>
  </ErrorBoundary>
);
