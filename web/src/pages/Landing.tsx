import { Link } from "react-router-dom";

/**
 * Public landing page.
 *
 * @returns The marketing screen and a sign-in link.
 */
export function Landing() {
  return (
    <div className="public landing">
      <header className="public-bar">
        <span className="brand">Harbor</span>
        <Link className="btn btn-primary" to="/login">
          Sign in
        </Link>
      </header>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Auto, truck, and home</p>
          <h1>Your policies, documents, and payments in one place.</h1>
          <p className="lede">
            Review cover, download documents, pay a pending installment, or send a message to your agent.
            This demonstration uses sample policies and does not contact a live carrier.
          </p>
          <Link className="btn btn-primary" to="/login">
            Sign in
          </Link>
          <p className="demo-note">Demo account: demo.customer@example.com / Demo1234!</p>
        </div>
      </section>
    </div>
  );
}
