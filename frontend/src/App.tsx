import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import DocumentDetail from './pages/DocumentDetail';
import DraftNew from './pages/DraftNew';
import DraftShow from './pages/DraftShow';
import DraftHistory from './pages/DraftHistory';
import Impact from './pages/Impact';
import ImpactReport from './pages/ImpactReport';
import Graph from './pages/Graph';
import DesignSystem from './pages/DesignSystem';

function App() {
  return (
    <Router>
      <div className="relative flex min-h-screen flex-col bg-background">
        <Header />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/documents/:id" element={<DocumentDetail />} />
            <Route path="/draft" element={<DraftNew />} />
            <Route path="/draft/:id" element={<DraftShow />} />
            <Route path="/drafts" element={<DraftHistory />} />
            <Route path="/impact" element={<Impact />} />
            <Route path="/impact/:id" element={<ImpactReport />} />
            <Route path="/graph" element={<Graph />} />
            <Route path="/design-system" element={<DesignSystem />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
