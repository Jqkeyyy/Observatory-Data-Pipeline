
import heroImg from './assets/logoMain.jpg'
import './App.css'
import { useEffect, useRef, useState } from 'react'
{/*import Login from './Login.jsx'*/}
function App() {

  //pull in imges for the carousel
  const [images, setImages] = useState([])
  useEffect(() => {
    fetch('/api/images')
      .then((res) => res.json())
      .then((data) =>
        setImages(data.slice(0, 10).map((img) => ({ name: `${img.target} - ${img.night_of}`, url: img.url })))
      )
      .catch((err) => console.error('Could not load images:', err))
  }, [])
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
          <a id="signinpage" href="/signin.html">Sign In</a>
          <a id="signUp" href="/signup.html">Sign Up</a>
        </div>
      </nav>

      {/*Center of landing page. Introduces the website and purpose */}
      <section id="center">
        <div className="hero">
          <img src={heroImg} className="base" width="900" height="402" alt="" />
        </div>
        <div>
          <h1>Whitewater Observatory Archive</h1>
          <p>
            Browse astronomical observations captured by the
            University of Wisconsin-Whitewater Observatory.
          </p>
        </div>
        <button id="searchButton"
          type="button"
          className="search"
          onClick={() => { location.href = '/search.html' }} // Opens search bar
        >
          Explore Archive 
        </button>
        {/* login moving to separate login and signup page
        <Login />*/}
      </section>

      <section className="carousel-section">
        <h2>Recent Observations</h2>

        <div className="carousel">
            <div className="carousel-move"> {/*This is just a placeholder for now */}
              {images.map(({name, url}) => (
                <img key={url} src={url} alt={name} />
              ))}
            </div>
              <div aria-hidden className="carousel-move">
                {images.map(({name, url}) => (
                <img key={url} src={url} alt={name} />
              ))}
              </div>
        
       </div>
      </section>
    </>
  )
}

export default App
