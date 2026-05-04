import { NavLink, Route, Routes } from "react-router-dom";

import Admin from "./pages/Admin";
import Company from "./pages/Company";
import CompanyMatches from "./pages/CompanyMatches";
import Home from "./pages/Home";
import HowItWorks from "./pages/HowItWorks";
import Matches from "./pages/Matches";
import Signup from "./pages/Signup";
import Stats from "./pages/Stats";

export default function App() {
  return (
    <>
      <nav className="nav">
        <span className="brand">StudentFlow</span>
        <NavLink to="/" end>
          Accueil
        </NavLink>
        <NavLink to="/how-it-works">Comment ça marche</NavLink>
        <NavLink to="/student">Étudiant</NavLink>
        <NavLink to="/company">Entreprise</NavLink>
        <NavLink to="/stats">Stats</NavLink>
        <NavLink to="/admin">Admin</NavLink>
        <span className="spacer" />
      </nav>
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/how-it-works" element={<HowItWorks />} />
          {/* Student funnel (alias /signup kept for backward compat) */}
          <Route path="/student" element={<Signup />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/matches" element={<Matches />} />
          <Route path="/matches/:studentId" element={<Matches />} />
          {/* Company funnel */}
          <Route path="/company" element={<Company />} />
          <Route path="/company/matches" element={<CompanyMatches />} />
          <Route path="/company/matches/:offerId" element={<CompanyMatches />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
    </>
  );
}
