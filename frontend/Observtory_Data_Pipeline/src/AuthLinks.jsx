import { signOut, useCurrentUser } from './auth.js'

// Goes inside <div className="nav-links">. Shows "Sign In" when signed out,
// or the person's name, an Admin link (admins only) and "Sign Out" when signed in.
function AuthLinks() {
  const user = useCurrentUser()

  if (user === undefined) return null // still checking, so the nav doesn't flash "Sign In"

  if (user === null) {
    // Come back to this page after signing in (unless we're already on the sign-in page)
    const here = location.pathname + location.search
    const href = location.pathname === '/signin.html' ? '/signin.html' : `/signin.html?next=${encodeURIComponent(here)}`
    return <a id="signIn" href={href}>Sign In</a>
  }

  return (
    <>
      {user.role === 'admin' && <a href="/admin.html">Admin</a>}
      <span style={{ color: 'white' }}>{user.name}</span>
      <a
        href="/"
        onClick={(e) => {
          e.preventDefault()
          signOut()
        }}
      >
        Sign Out
      </a>
    </>
  )
}

export default AuthLinks
