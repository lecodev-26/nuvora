import React, { createContext, useState, useContext } from 'react';

const BotContext = createContext();

export const BotProvider = ({ children }) => {
  const [bots, setBots] = useState([]);
  const [selectedBot, setSelectedBot] = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <BotContext.Provider value={{
      bots,
      setBots,
      selectedBot,
      setSelectedBot,
      loading,
      setLoading,
    }}>
      {children}
    </BotContext.Provider>
  );
};

export const useBot = () => useContext(BotContext);

