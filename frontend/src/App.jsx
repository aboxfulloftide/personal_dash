import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Routes>
          <Route path="/" element={<div className="p-4 text-gray-900 dark:text-white">Personal Dash - Coming Soon</div>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;