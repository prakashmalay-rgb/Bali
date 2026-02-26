import { createRoot } from "react-dom/client";
import { ErrorBoundary } from "react-error-boundary";
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
      window.location.reload();
    }}
  >
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
  </ErrorBoundary>
);
