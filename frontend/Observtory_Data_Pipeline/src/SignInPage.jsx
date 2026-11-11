import "./SignInPage.css"
import logoImg from './assets/observatoryLogo.png'

function SignInPage() {
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
          <a id="signIn" href="/signin.html">Sign In</a>
          <a id="signUp" href="/signup.html">Sign Up</a>
        </div>
      </nav>
      {/* Block for sign in page. */}
      <div className="signin-page">
        <div className="signin-card">

          <h1>Sign In</h1>

          <p className="signin-description">
            Sign in to access the Whitewater Observatory Archive.
          </p>

          <form className="signin-form">

            <label htmlFor="email">
              Email
            </label>

            <input
              id="email"
              type="email"
              placeholder="Enter your email"
            />

            <label htmlFor="password">
              Password
            </label>

            <input
              id="password"
              type="password"
              placeholder="Enter your password"
            />

            <button type="submit">
              Sign In
            </button>

          </form>

          <p className="signup-link">
            Don't have an account?{' '}
            <a href="/signup.html">
              Create one here
            </a>
          </p>

        </div>
      </div>
    </>
  )
}

export default SignInPage