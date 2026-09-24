import React from 'react';
import { useParams } from 'react-router-dom';

const CreatorChannels = () => {
  const { botId } = useParams();
  return (
    <div className="space-y-6">
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
        <h2 className="text-xl font-semibold mb-2">📡 Canales</h2>
        <p className="text-white/60 text-sm">
          Placeholder — Bot #{botId}. Se implementa en 14.12.16.
        </p>
      </div>
    </div>
  );
};

export default CreatorChannels;
