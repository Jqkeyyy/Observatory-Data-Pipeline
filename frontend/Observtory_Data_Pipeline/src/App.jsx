
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
          <h1>Whitewater Observatory Archive</h1>
          <p>
            Browse astronomical observations captured by the
            University of Wisconsin-Whitewater Observatory.
          </p>
        </div>
        <button
          type="button"
          className="search"
          onClick={() => { location.href = '/search.html' }} // Opens search bar
        >
          Explore Archive 
        </button>
      </section>

      <section className="carousel-section">
        <h2>Recent Observations</h2>

        <div className="carousel">
           <div className="carousel-move"> {/*This is just a placeholder for now */}
         <img src="/images/SuperMarioGalaxy.jpg" alt="sample 1"></img>
         <img src="/images/Stars example.jpg" alt="sample 2"></img>
         <img src="/images/SuperMarioGalaxy.jpg" alt="sample 3"></img>
         <img src="/images/Stars example.jpg" alt="sample 4"></img>
         <img src="/images/SuperMarioGalaxy.jpg" alt="sample 5"></img>
         <img src="/images/Stars example.jpg" alt="sample 6"></img>
         <img src="/images/SuperMarioGalaxy.jpg" alt="sample 7"></img>
         </div>
         <div aria-hidden className="carousel-move">
         <img src="/images/SuperMarioGalaxy.jpg" alt="sample 1"></img>
         <img src="/images/Stars example.jpg" alt="sample 2"></img>
         <img src="/images/SuperMarioGalaxy.jpg" alt="sample 3"></img>
         <img src="/images/Stars example.jpg" alt="sample 4"></img>
         <img src="/images/SuperMarioGalaxy.jpg" alt="sample 5"></img>
         <img src="/images/Stars example.jpg" alt="sample 6"></img>
         <img src="/images/SuperMarioGalaxy.jpg" alt="sample 7"></img>
         </div>
        
       </div>
      </section>
    </>
  )
}

export default App
