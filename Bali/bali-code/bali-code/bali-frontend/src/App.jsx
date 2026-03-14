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
import SubCategories from "./components/services/Subcategories";
import ServiceItems from "./components/services/serviceItems";
import PrivacyPolicy from "./components/termspages/privacy-policy/PrivacyPolicy";
import TermsConditons from "./components/termspages/terms-conditions/TermsConditons";
import ContactUs from "./components/termspages/privacy-policy/contact-us/ContactUs";
import GuestActivity from "./page/dashboard/GuestActivity";
import Welcome from "./page/welcome";

import DashboardLayout from "./page/dashboard/DashboardLayout";
import DashboardMain from "./page/dashboard/DashboardMain";
import DashboardLogin from "./page/dashboard/Login";
import DashboardChats from "./page/dashboard/DashboardChats";
import PassportVerification from "./page/dashboard/PassportVerification";
import PromoManagement from "./page/dashboard/PromoManagement";
import FAQManagement from "./page/dashboard/FAQManagement";
import MessageAutomations from "./page/dashboard/MessageAutomations";
import BookingsView from "./page/dashboard/BookingsView";
import IssuesView from "./page/dashboard/IssuesView";
import CheckinsView from "./page/dashboard/CheckinsView";
import VillaProfile from "./page/dashboard/VillaProfile";
import FeedbackView from "./page/dashboard/FeedbackView";
import CustomerBucket from "./page/dashboard/CustomerBucket";
import VillaBucket from "./page/dashboard/VillaBucket";
import PaymentBucket from "./page/dashboard/PaymentBucket";
import ServiceBucket from "./page/dashboard/ServiceBucket";
import ContentLibrary from "./page/dashboard/ContentLibrary";
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
        path: "/login",
        element: <Navigate to="/admin/login" replace />
      },
      {
        path: "/admin/login",
        element: <DashboardLogin />
      },
      {
        path: "/welcome",
        element: <Welcome />
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
      },
      {
        path: "bookings",
        element: <BookingsView />,
      },
      {
        path: "issues",
        element: <IssuesView />,
      },
      {
        path: "checkins",
        element: <CheckinsView />,
      },
      {
        path: "feedback",
        element: <FeedbackView />,
      },
      {
        path: "villa-profile",
        element: <VillaProfile />,
      },
      {
        path: "promos",
        element: <PromoManagement />,
      },
      {
        path: "faqs",
        element: <FAQManagement />
      },
      {
        path: "automations",
        element: <MessageAutomations />
      },
      {
        path: "customers",
        element: <CustomerBucket />
      },
      {
        path: "villas",
        element: <VillaBucket />
      },
      {
        path: "payments",
        element: <PaymentBucket />
      },
      {
        path: "services",
        element: <ServiceBucket />
      },
      {
        path: "content",
        element: <ContentLibrary />
      }
    ],
  },
]);
export default AppLayout;
