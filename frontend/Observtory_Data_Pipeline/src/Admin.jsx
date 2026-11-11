import { useState } from 'react'
import './Admin.css'

// Fastest allowed is 2 pictures a minute
const maxPictures = { minute: 2, hour: 120 }

// Remove once hooked up, just for show
const users = [
  { id: 1, email: 'StudentUser@uww.edu', role: 'user' },
  { id: 2, email: 'OtherStudent@uww.edu', role: 'user' },
  { id: 3, email: 'nine@uww.edu', role: 'admin' },
]

const queueTabs = ['Upcoming', 'Current', 'Done']

// no handlers
function Admin() {
  const [start, setStart] = useState('')
  const [pictureUnit, setPictureUnit] = useState('minute')
  const [queueTab, setQueueTab] = useState('Upcoming')

  function submitJob(e) {
    e.preventDefault()
    const form = new FormData(e.target)
    const [startDate, startTime] = form.get('start').split('T')
    const [endDate, endTime] = form.get('end').split('T')
    const job = {
      startDate,
      startTime,
      endDate,
      endTime,
      pictures: Number(form.get('pictures')),
      frequency: form.get('frequency'), // 'minute' or 'hour'
    }
    console.log(job) // this is where you'll want to send to serv
  }

  return (
    <>
      <header className="admin-bar">
        <h1>Admin</h1>
        <a href="/">Back to archive</a>
      </header>

      <div className="admin-columns">
      <div>
      <section className="admin-section">
        <h2>Session settings</h2>
        <form className="settings" onSubmit={submitJob}>
          <label>
            Start
            <input name="start" type="datetime-local" required onChange={(e) => setStart(e.target.value)} />
          </label>
          <label>
            End
            <input name="end" type="datetime-local" required min={start} />
          </label>
          <label>
            Pictures
            <span className="field">
              <input name="pictures" type="number" min="0" max={maxPictures[pictureUnit]} required defaultValue="1" />
              <select name="frequency" value={pictureUnit} onChange={(e) => setPictureUnit(e.target.value)}>
                <option value="hour">per hour</option>
                <option value="minute">per minute</option>
              </select>
            </span>
          </label>
          <button type="submit">Submit Job</button>
        </form>
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
          {queueTabs.map((tab) => (
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
        {/* Empty for now */}
        <div className="queue-list" role="tabpanel" aria-label={queueTab}></div>
      </section>
      </div>
    </>
  )
}

export default Admin
