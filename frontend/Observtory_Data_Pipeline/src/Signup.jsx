import './Signup.css'

function Signup(){
return (
    <form className='signup' onSubmit={(e) => e.preventDefault()}>
        <h2>Create An Account</h2>
      <input type="text" name="username" placeholder="Username" autoComplete="username" />
      <input type="email" name="email" placeholder="Email" autoComplete="email" />
      <input type="password" name="password" placeholder="Password" autoComplete="new-password" />

      <button type='submit'>Sign Up</button>
    
    {/* <p>Already have an account? <a href="login.html">Log In</a></p> 
    This will go in once the login.html page is set up*/}
    </form>
  )
}



export default Signup
