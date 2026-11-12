import "./SignInPage.css"
import AuthLinks from "./AuthLinks.jsx"
import { googleSignInUrl, useCurrentUser } from "./auth.js"

// What to show when the backend sends someone back with ?login_error=
const loginErrors = {
  cancelled: "Sign-in was cancelled. Try again whenever you're ready.",
  unverified_email: "Google hasn't verified that email address yet.",
  domain_not_allowed: "That email address isn't allowed to sign in here.",
  email_in_use: "That email is already linked to a different Google account.",
}

function SignInPage() {
  const user = useCurrentUser()
  const params = new URLSearchParams(location.search)
  const requested = params.get("next") || "/"
  // Only pages on this site (not "//other-site.com" or "javascript:...")
  const next = requested.startsWith("/") && !requested.startsWith("//") ? requested : "/"
  const errorCode = params.get("login_error")
  const error = errorCode && (loginErrors[errorCode] || "Sign-in didn't work. Try again.")

  return (
    <>
      {/*Navigation bar that will sit at the top of every page to navigate from page to page. */}
      <nav className="navbar">
        <div className="nav-logo">
          Whitewater Observatory
        </div>

        <div className="nav-links">
          <a id="Home" href="/">Home</a>
          <a id="Search" href="/search.html">Search</a>
          <AuthLinks />
        </div>
      </nav>

      <div className="signin-page">
        <div className="signin-card">

          <h1>Sign In</h1>

          {user ? (
            <>
              <p className="signin-description">
                You're signed in as {user.email}.
              </p>

              <a className="google-button" href={next}>
                Continue
              </a>
            </>
          ) : (
            <>
              <p className="signin-description">
                Sign in to access the Whitewater Observatory Archive.
              </p>

              {error && (
                <p className="signin-error" role="alert">
                  {error}
                </p>
              )}

              {/* A plain link, not fetch: the browser has to actually go to Google's sign-in page */}
              <a className="google-button" href={googleSignInUrl(next)}>
                Sign in with Google
              </a>

              <p className="signup-link">
                First time here? Signing in with Google creates your account.
              </p>
            </>
          )}

        </div>
      </div>
    </>
  )
}

export default SignInPage
