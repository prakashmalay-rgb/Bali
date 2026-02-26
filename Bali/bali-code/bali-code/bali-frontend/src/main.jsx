import { createRoot } from "react-dom/client";
import { ErrorBoundary } from "react-error-boundary";
import { HelmetProvider } from "react-helmet-async";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import "./style/main.scss";
import "./main.css";
import "sweetalert2/dist/sweetalert2.min.css";
import AppLayout from "./App.jsx";
import ErrorFallback from "./components/ErrorFallback";

const container = document.getElementById("root");
const root = createRoot(container);

root.render(
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
