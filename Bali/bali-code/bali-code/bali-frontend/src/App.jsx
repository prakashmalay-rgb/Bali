import { Outlet, RouterProvider, createBrowserRouter } from "react-router-dom";
import NotFound from "./page/notFound";
import Login from "./page/account/login";
import ResetPassword from "./page/account/resetPassword";
import Verify from "./page/account/verify";
import Forget from "./page/account/forget";
import Register from "./page/account/register";
import Components from "./components/components";
import Home from "./page/home";
import Chat from "./components/chatbot/chat";
import TripServices from "./components/services/Categories";
import SubCategories from "./components/services/Subcategories"
import ServiceItems from "./components/services/serviceItems";
import PrivacyPolicy from "./components/termspages/privacy-policy/PrivacyPolicy";
import TermsConditons from "./components/termspages/terms-conditions/TermsConditons";
import ContactUs from "./components/termspages/privacy-policy/contact-us/ContactUs";
import GuestActivity from "./page/dashboard/GuestActivity";

import DashboardLayout from "./page/dashboard/DashboardLayout";
import DashboardMain from "./page/dashboard/DashboardMain";
import DashboardLogin from "./page/dashboard/Login";
import DashboardChats from "./page/dashboard/DashboardChats";
import PassportVerification from "./page/dashboard/PassportVerification";
import { Navigate } from "react-router-dom";
import { LanguageProvider } from "./context/LanguageContext";
import PageTransition from "./components/layout/PageTransition";
import { AnimatePresence } from "framer-motion";
import { useLocation } from "react-router-dom";

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem("easybali_token");
  if (!token) {
    return <Navigate to="/admin/login" replace />;
  }
  return children;
};

const AnimatedLayout = () => {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <PageTransition key={location.pathname}>
        <Outlet />
      </PageTransition>
    </AnimatePresence>
  );
};

const AppLayout = () => {
  return (
    <LanguageProvider>
      <RouterProvider router={appRouter} />
    </LanguageProvider>
  );
};

const appRouter = createBrowserRouter([
  {
    element: <AnimatedLayout />,
    children: [
      {
        path: "*",
        element: <NotFound />,
      },
      {
        path: "/",
        element: <Home />,
      },
      {
        path: "/admin/login",
        element: <DashboardLogin />
      },
      {
        path: "/categories",
        element: <TripServices />
      },
      {
        path: "/subcategories",
        element: <SubCategories />
      },
      {
        path: "/serviceitems",
        element: <ServiceItems />
      },
      {
        path: "/privacy-policy",
        element: <PrivacyPolicy />
      },
      {
        path: "/terms-and-conditions",
        element: <TermsConditons />
      },
      {
        path: "/contact-us",
        element: <ContactUs />
      },
      {
        path: "/chatbot",
        element: <Chat />,
      },
    ]
  },
  // Dashboard Routes
  {
    path: "/dashboard",
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: "/dashboard", // Root of dashboard points to overview
        element: <DashboardMain />,
      },
      {
        path: "guests",
        element: <GuestActivity />,
      },
      {
        path: "chats",
        element: <DashboardChats />,
      },
      {
        path: "passports",
        element: <PassportVerification />,
      }
    ],
  },
]);
export default AppLayout;
