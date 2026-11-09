import './Admin.css'

// Remove once hooked up, just for show
const users = [
  { id: 1, email: 'StudentUser@uww.edu', role: 'user' },
  { id: 2, email: 'OtherStudent@uww.edu', role: 'user' },
  { id: 3, email: 'nine@uww.edu', role: 'admin' },
]

// no handlers
function Admin() {
  return (
    <>
      <header className="admin-bar">
        <h1>Admin</h1>
        <a href="/">Back to archive</a>
      </header>

      <section className="admin-section">
        <h2>Session settings</h2>
        <div className="settings">
          <label>
            Total time
            <span className="field">
              <input type="number" min="0" defaultValue="2" />
              <select defaultValue="hours">
                <option value="hours">hours</option>
                <option value="minutes">minutes</option>
              </select>
            </span>
          </label>
          <label>
            Pictures
            <span className="field">
              <input type="number" min="0" defaultValue="1" />
              <select defaultValue="minute">
                <option value="hour">per hour</option>
                <option value="minute">per minute</option>
                <option value="second">per second</option>
              </select>
            </span>
          </label>
          <button type="button">Save settings</button>
        </div>
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
