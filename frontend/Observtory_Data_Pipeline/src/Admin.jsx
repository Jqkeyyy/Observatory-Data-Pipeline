import { useState, useEffect } from 'react'
import { ScheduleSession } from './components'
import './Admin.css'

const users = [
  { id: 1, email: 'StudentUser@uww.edu', role: 'user' },
  { id: 2, email: 'OtherStudent@uww.edu', role: 'user' },
  { id: 3, email: 'nine@uww.edu', role: 'admin' },
]

function Admin() {
  const [sessionJobs, setSessionJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')

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
    fetchJobs() // Refresh the table list
  }

  return (
    <>
      <header className="admin-bar">
        <h1>Admin</h1>
        <a href="/">Back to archive</a>
      </header>

      {/* Action Bar for Opening Modal */}
      <section className="admin-section" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Observatory Session Management</h2>
        <button type="button" onClick={() => { setIsModalOpen(true); setSuccessMsg(''); }}>
          Schedule New Session
        </button>
      </section>

      {successMsg && (
        <div className="admin-section" style={{ color: '#2ecc71', fontWeight: 600 }}>
          {successMsg}
        </div>
      )}

      {/* Render the extracted modal component */}
      <ScheduleSession 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSuccess={handleModalSuccess} 
      />

      {/* Live Session Jobs Management Section */}
      <section className="admin-section">
        <h2>Session Jobs (Current & Completed)</h2>
        <table className="users">
          <thead>
            <tr>
              <th>ID</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Interval</th>
              <th>Scheduled For</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '16px' }}>Loading jobs...</td>
              </tr>
            ) : sessionJobs.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '16px' }}>No session jobs found.</td>
              </tr>
            ) : (
              sessionJobs.map((job) => (
                <tr key={job.id}>
                  <td>#{job.id}</td>
                  <td>
                    <span className={`status-badge ${job.status}`}>
                      {job.status}
                    </span>
                  </td>
                  <td>{job.duration_seconds}s</td>
                  <td>{job.interval_seconds}s</td>
                  <td>{job.scheduled_for ? new Date(job.scheduled_for).toLocaleString() : 'Immediate'}</td>
                  <td>{job.created_at ? new Date(job.created_at).toLocaleString() : '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
    </>
  )
}

export default Admin