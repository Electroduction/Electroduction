import './index.css';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Projects from './components/Projects';
import Stats from './components/Stats';
import Leaderboard from './components/Leaderboard';
import Contact from './components/Contact';
import Footer from './components/Footer';

export default function App() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Projects />
        <Stats />
        <Leaderboard />
        <Contact />
      </main>
      <Footer />
    </>
  );
}
