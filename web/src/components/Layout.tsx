import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

const LINKS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/policies", label: "My Policies" },
  { to: "/documents", label: "My Documents" },
  { to: "/payments", label: "My Payments" },
  { to: "/contact", label: "Contact Agent" },
];

/**
 * Signed-in shell with the left navigation.
 *
 * @returns The portal frame and the active page.
 */
export function Layout() {
  const { profile, signOut } = useAuth();
  return (
    <div className="shell">
      <aside className="sidebar">
        <p className="brand">Harbor</p>
        <p className="brand-sub">Policy portal</p>
        <nav className="menu" aria-label="Portal">
          {LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} className={({ isActive }) => (isActive ? "menu-link active" : "menu-link")}>
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <p className="signed-in">{profile?.full_name ?? "Customer"}</p>
          <button type="button" className="btn btn-ghost" onClick={signOut}>
            Sign out
          </button>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
