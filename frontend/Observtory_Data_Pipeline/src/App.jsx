
import heroImg from './assets/logoMain.jpg'
import './App.css'

function App() {

  return (
    <>
      <section id="center">
        <div className="hero">
          <img src={heroImg} className="base" width="900" height="402" alt="" />
        </div>
        <div>
          <h1>Get started</h1>
          <p>
            Database for University of Whitewater-Wisconsin Observatory
          </p>
        </div>
        <button
          type="button"
          className="search"
          onClick={() => { location.href = '/search.html' }} // Opens search bar
        >
          Search
        </button>
      </section>

      <div className="ticks"></div>
      <section id="spacer"></section>
    </>
  )
}

export default App
