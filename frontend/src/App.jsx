import { useState } from 'react';
import RoleSelection from './components/RoleSelection';
import HRDashboard from './components/HRDashboard';
import StudentPortal from './components/StudentPortal';

function App() {
  const [role, setRole] = useState(null); // 'HR', 'Student', or null

  return (
    <div className="app-container">
      {!role && <RoleSelection onSelectRole={setRole} />}
      {role === 'HR' && <HRDashboard onExit={() => setRole(null)} />}
      {role === 'Student' && <StudentPortal onExit={() => setRole(null)} />}
    </div>
  );
}

export default App;
