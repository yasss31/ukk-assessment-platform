import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { NewAssessment } from './pages/NewAssessment';
import { Assessments } from './pages/Assessments';
import { AssessmentDetail } from './pages/AssessmentDetail';
import { Rubrics } from './pages/Rubrics';
import { AutoPlay } from './pages/AutoPlay';
import { Participants } from './pages/Participants';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { User } from './types';
import { api } from './api';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [activeParam, setActiveParam] = useState<any>(null);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('ukk_token');
      if (token) {
        try {
          const user = await api.getMe();
          setCurrentUser(user);
        } catch {
          localStorage.removeItem('ukk_token');
          localStorage.removeItem('ukk_user');
          setCurrentUser(null);
        }
      }
      setCheckingAuth(false);
    };
    checkAuth();
  }, []);

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
    setActiveTab('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('ukk_token');
    localStorage.removeItem('ukk_user');
    setCurrentUser(null);
  };

  const handleNavigate = (tab: string, param?: any) => {
    setActiveTab(tab);
    setActiveParam(param);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex items-center justify-center text-xs text-slate-400">
        Memverifikasi sesi pengguna...
      </div>
    );
  }

  if (!currentUser) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      <Navbar user={currentUser} onLogout={handleLogout} />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar activeTab={activeTab} setActiveTab={(tab) => handleNavigate(tab)} />

        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {activeTab === 'dashboard' && <Dashboard onNavigate={handleNavigate} />}
          {activeTab === 'new-assessment' && <NewAssessment onNavigate={handleNavigate} />}
          {activeTab === 'assessments' && <Assessments onNavigate={handleNavigate} />}
          {activeTab === 'assessment-detail' && (
            <AssessmentDetail
              sessionId={activeParam}
              onBack={() => handleNavigate('assessments')}
            />
          )}
          {activeTab === 'rubrics' && <Rubrics />}
          {activeTab === 'autoplay' && <AutoPlay />}
          {activeTab === 'participants' && <Participants />}
          {activeTab === 'reports' && <Reports />}
          {activeTab === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
};

export default App;
