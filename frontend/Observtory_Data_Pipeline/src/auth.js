// Who's signed in, for any page. The backend does the actual Google sign-in (see backend/AUTH.md).
import { useEffect, useState } from 'react'

// undefined = still checking, null = signed out, otherwise { id, email, name, picture_url, role, ... }
export function useCurrentUser() {
  const [user, setUser] = useState(undefined)

  useEffect(() => {
    fetch('/api/auth/me')
      .then((res) => (res.ok ? res.json() : null))
      .then(setUser)
      .catch(() => setUser(null))
  }, [])

  return user
}

// Where the "Sign in with Google" button goes. next = the page to come back to afterwards
export function googleSignInUrl(next = '/') {
  return `/api/auth/login?next=${encodeURIComponent(next)}`
}

export async function signOut() {
  await fetch('/api/auth/logout', { method: 'POST' })
  location.href = '/'
}
