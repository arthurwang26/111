import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import EldersPage from './pages/Elders';
import ElderDetailPage from './pages/ElderDetail';
import LogsPage from './pages/Logs';
import CamerasPage from './pages/Cameras';
import SettingsPage from './pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/elders" element={<EldersPage />} />
          <Route path="/elders/:id" element={<ElderDetailPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/cameras" element={<CamerasPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
