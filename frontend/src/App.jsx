import React from 'react';
import { BotProvider } from './context/BotContext';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <BotProvider>
      <Dashboard />
    </BotProvider>
  );
}

export default App;
