import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { Toaster } from 'sonner';
import { HomePage } from './pages/HomePage';
import { ReportPage } from './pages/ReportPage';

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<HomePage />} />
        <Route path="/report/:analysisId" element={<ReportPage />} />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster theme="dark" position="bottom-right" richColors />
      <AnimatedRoutes />
    </BrowserRouter>
  );
}
