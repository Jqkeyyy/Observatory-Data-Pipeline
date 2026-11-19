
import heroImg from './assets/logoMain.jpg'
import './App.css'
import AuthLinks from './AuthLinks.jsx'
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
          <AuthLinks />
        </div>
      </nav>

      {/*Center of landing page. Introduces the website and purpose */}
      <section id="center">
        <div>
          <h1>Whitewater Observatory Archive</h1>
        </div>
       
        {/* login moving to separate login and signup page
        <Login />*/}
      </section>

      <section className="carousel-section">

        <div className="carousel">
            <div className="carousel-move"> {/*Update with premium images tags*/}
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
       <button id="searchButton"
          type="button"
          className="search"
          onClick={() => { location.href = '/search.html' }} // Opens search bar
        >
          Explore Archive 
        </button>
    </>
  )
}

export default App
