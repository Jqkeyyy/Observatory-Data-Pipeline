import './Login.css'

// Reusable login box: import Login from './Login.jsx' and drop <Login /> anywhere
function Login() {
  return (
    <form className="login" onSubmit={(e) => e.preventDefault()}>
      <input type="text" name="username" placeholder="Username" autoComplete="username" />
      <input type="password" name="password" placeholder="Password" autoComplete="current-password" />
      <a href="#">Forgot password</a>
    </form>
  )
}

export default Login
