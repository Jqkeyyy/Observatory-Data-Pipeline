import { useState, useEffect } from 'react'
import { ScheduleSession } from './components'
import './Admin.css'

// Remove once hooked up, just for show
const users = [
  { id: 1, email: 'StudentUser@uww.edu', role: 'user' },
  { id: 2, email: 'OtherStudent@uww.edu', role: 'user' },
  { id: 3, email: 'nine@uww.edu', role: 'admin' },
]

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
  const [sessionJobs, setSessionJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')
  const [queueTab, setQueueTab] = useState('Upcoming')

  const fetchJobs = () => {
    fetch('/api/sessions/jobs')
      .then((res) => res.json())
      .then((data) => {
        setSessionJobs(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to fetch session jobs:', err)
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchJobs()
  }, [])

  const handleModalSuccess = (msg) => {
    setSuccessMsg(msg)
    fetchJobs() // Refresh the queue
  }

  const cancelJob = (id) => {
    fetch(`/api/sessions/jobs/${id}`, { method: 'DELETE' })
      .then(() => fetchJobs())
      .catch((err) => console.error('Failed to cancel job:', err))
  }

  const jobsInTab = sessionJobs.filter((job) => queueTabs[queueTab].includes(job.status))

  return (
    <>
      <header className="admin-bar">
        <h1>Admin</h1>
        <a href="/">Back to archive</a>
      </header>

      <div className="admin-columns">
        <div>
          <section className="admin-section">
            <h2>Observatory sessions</h2>
            <button type="button" onClick={() => { setIsModalOpen(true); setSuccessMsg(''); }}>
              Schedule New Session
            </button>
            {successMsg && <p className="success-msg">{successMsg}</p>}
          </section>

          <section className="admin-section">
            <h2>Users</h2>
            <table className="users">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Role</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.email}</td>
                    <td>
                      <select defaultValue={user.role}>
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td className="row-actions">
                      <button type="button" className="danger">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </div>

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
                {loading ? (
                  <tr>
                    <td colSpan="6" className="queue-empty">Loading jobs...</td>
                  </tr>
                ) : jobsInTab.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="queue-empty">No {queueTab.toLowerCase()} jobs.</td>
                  </tr>
                ) : (
                  jobsInTab.map((job) => (
                    <tr key={job.id}>
                      <td>#{job.id}</td>
                      <td>
                        <span className={`status-badge ${job.status}`}>{job.status}</span>
                      </td>
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
                          <button type="button" className="danger" onClick={() => cancelJob(job.id)}>
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
      </div>

      {/* Render the extracted modal component */}
      <ScheduleSession
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleModalSuccess}
      />
    </>
  )
}

export default Admin
