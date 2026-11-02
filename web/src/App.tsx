import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RequireAuth } from "./components/RequireAuth";
import { Contact } from "./pages/Contact";
import { Documents } from "./pages/Documents";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { ManagePolicy } from "./pages/ManagePolicy";
import { Payments } from "./pages/Payments";
import { Dashboard, Policies } from "./pages/Policies";
import { RenewalDetails } from "./pages/RenewalDetails";

/**
 * Application routes.
 *
 * @returns The route tree.
 */
export function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/policies" element={<Policies />} />
          <Route path="/policies/:policyNumber" element={<ManagePolicy />} />
          <Route path="/policies/:policyNumber/renewal" element={<RenewalDetails />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/payments" element={<Payments />} />
          <Route path="/contact" element={<Contact />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
