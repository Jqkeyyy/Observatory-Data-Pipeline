import { useEffect, useState } from 'react'
import './Admin.css'
import AuthLinks from './AuthLinks.jsx'
import { useCurrentUser } from './auth.js'
import { ScheduleSession } from './components'

// Which job statuses show under each queue tab
const queueTabs = {
  Upcoming: ['pending'],
  Current: ['running'],
  Done: ['completed', 'error'],
}

function formatSeconds(seconds) {
  if (seconds % 3600 === 0) return `${seconds / 3600}h`
  if (seconds % 60 === 0) return `${seconds / 60}m`
  return `${seconds}s`
}

function Admin() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')
  const me = useCurrentUser()

  // Signed out: send them to sign in, then back here
  useEffect(() => {
    if (me === null) location.replace('/signin.html?next=/admin.html')
  }, [me])

  /*Navigation bar that will sit at the top of every page to navigate from page to page. */
  const nav = (
    <nav className="navbar">
      <div className="nav-logo">
        Whitewater Observatory
      </div>

      <div className="nav-links">
        <a href="/">Home</a>
        <a href="/search.html">Search</a>
        <AuthLinks />
      </div>
    </nav>
  )

  // Hiding the page is just so people don't see controls they can't use.
  // The real protection is the backend: /api/users only answers admins.
  if (!me) return nav // still checking, or on the way to the sign-in page

  if (me.role !== 'admin') {
    return (
      <>
        {nav}
        <main className="admin-content">
          <h1 className="admin-title">Admins only</h1>
          <p className="admin-note">
            You're signed in as {me.email}, which isn't an admin account.
            Ask a professor or another admin to change your role.
          </p>
          <a className="admin-link" href="/">Back to home</a>
        </main>
      </>
    )
  }

  return (
    <>
      {nav}

      <main className="admin-content">
      <h1 className="admin-title">Admin</h1>

      <div className="admin-columns">
      <div>
      <section className="admin-section">
        <h2>Observatory sessions</h2>
        <button type="button" onClick={() => { setIsModalOpen(true); setSuccessMsg('') }}>
          Schedule New Session
        </button>
        {successMsg && <p className="success-msg">{successMsg}</p>}
      </section>

      <section className="admin-section">
        <h2>Users</h2>
        <UsersTable me={me} />
      </section>
      </div>

      <JobQueue refreshKey={successMsg} />
      </div>
      </main>

      <ScheduleSession
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={setSuccessMsg}
      />
    </>
  )
}

// Capture jobs from the server, split into Upcoming / Current / Done.
// refreshKey changes after a new job is scheduled, which reloads the list.
function JobQueue({ refreshKey }) {
  const [jobs, setJobs] = useState(null) // null = still loading
  const [error, setError] = useState('')
  const [queueTab, setQueueTab] = useState('Upcoming')

  function loadJobs() {
    return fetch('/api/sessions/jobs')
      .then((res) => (res.ok ? res.json() : Promise.reject(res)))
      .then(setJobs)
      .catch(() => setError("Couldn't load the queue. Try refreshing the page."))
  }

  useEffect(() => {
    loadJobs()
  }, [refreshKey])

  async function cancelJob(job) {
    if (!confirm(`Cancel job #${job.id}?`)) return
    setError('')
    const res = await fetch(`/api/sessions/jobs/${job.id}`, { method: 'DELETE' })
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      return setError(body?.error || 'Something went wrong. Try again.')
    }
    loadJobs()
  }

  const jobsInTab = (jobs ?? []).filter((job) => queueTabs[queueTab].includes(job.status))

  return (
    <section className="admin-section queue">
      <h2>Queue</h2>
      <div className="queue-tabs" role="tablist">
        {Object.keys(queueTabs).map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={queueTab === tab}
            onClick={() => setQueueTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
      {error && <p className="admin-error" role="alert">{error}</p>}
      <div className="queue-list" role="tabpanel" aria-label={queueTab}>
        <table className="users">
          <thead>
            <tr>
              <th>ID</th>
              <th>Status</th>
              <th>Starts</th>
              <th>Length</th>
              <th>Every</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {jobs === null ? (
              <tr><td colSpan="6" className="queue-empty">Loading jobs...</td></tr>
            ) : jobsInTab.length === 0 ? (
              <tr><td colSpan="6" className="queue-empty">No {queueTab.toLowerCase()} jobs.</td></tr>
            ) : (
              jobsInTab.map((job) => (
                <tr key={job.id}>
                  <td>#{job.id}</td>
                  <td><span className={`status-badge ${job.status}`}>{job.status}</span></td>
                  <td>
                    {job.scheduled_for
                      ? new Date(job.scheduled_for).toLocaleString()
                      : job.started_at
                        ? new Date(job.started_at).toLocaleString()
                        : 'Immediate'}
                  </td>
                  <td>{formatSeconds(job.duration_seconds)}</td>
                  <td>{formatSeconds(job.interval_seconds)}</td>
                  <td className="row-actions">
                    {job.status === 'pending' && (
                      <button type="button" className="danger" onClick={() => cancelJob(job)}>
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

// Everyone who has signed in, from the database. Admins can change roles and delete accounts.
// Permanent admins (ADMIN_EMAILS on the server, e.g. Dr. Nine) can't be changed or deleted here,
// and other admins have to be changed to User before they can be deleted.
function UsersTable({ me }) {
  const [users, setUsers] = useState(null) // null = still loading
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/users')
      .then((res) => (res.ok ? res.json() : Promise.reject(res)))
      .then(setUsers)
      .catch(() => setError("Couldn't load users. Try refreshing the page."))
  }, [])

  // Shows the backend's error message, e.g. "you can't change your own role"
  async function errorFrom(res) {
    const body = await res.json().catch(() => null)
    return body?.error || 'Something went wrong. Try again.'
  }

  async function changeRole(user, role) {
    const question = role === 'admin'
      ? `Make ${user.name} an admin? They'll be able to change capture settings and manage users.`
      : `Remove admin access from ${user.name}?`
    if (!confirm(question)) return // the dropdown snaps back on its own
    setError('')
    const res = await fetch(`/api/users/${user.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role }),
    })
    if (!res.ok) return setError(await errorFrom(res))
    const updated = await res.json()
    setUsers((list) => list.map((u) => (u.id === updated.id ? updated : u)))
  }

  async function deleteUser(user) {
    if (!confirm(`Delete ${user.email}? They can sign in again later as a normal user.`)) return
    setError('')
    const res = await fetch(`/api/users/${user.id}`, { method: 'DELETE' })
    if (!res.ok) return setError(await errorFrom(res))
    setUsers((list) => list.filter((u) => u.id !== user.id))
  }

  return (
    <>
      {error && <p className="admin-error" role="alert">{error}</p>}
      {users === null ? (
        !error && <p className="admin-note">Loading users...</p>
      ) : (
        <table className="users">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => {
              const isMe = user.id === me.id
              const locked = isMe || user.permanent_admin
              return (
                <tr key={user.id}>
                  <td>
                    {user.name}{isMe && ' (you)'}
                    {user.permanent_admin && <span className="user-tag">Permanent admin</span>}
                  </td>
                  <td>{user.email}</td>
                  <td>
                    <select
                      value={user.role}
                      disabled={locked}
                      title={
                        isMe ? "You can't change your own role"
                          : user.permanent_admin ? "Permanent admins are set on the server, not here"
                          : undefined
                      }
                      onChange={(e) => changeRole(user, e.target.value)}
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                  <td className="row-actions">
                    {!locked && (
                      <button
                        type="button"
                        className="danger"
                        disabled={user.role === 'admin'}
                        title={user.role === 'admin' ? 'Change their role to User first' : undefined}
                        onClick={() => deleteUser(user)}
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </>
  )
}

export default Admin
