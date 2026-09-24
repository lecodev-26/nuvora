import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import ChannelsPanel from '../../components/channels/ChannelsPanel';
import CreatorError from '../../components/creator/CreatorError';
import Spinner from '../../components/ui/Spinner';
import { botService } from '../../services/api';

/**
 * CreatorChannels — Página de Canales dentro de Creator Mode.
 *
 * Monta el ChannelsPanel existente (modal) abierto por defecto.
 * Al cerrar → vuelve al Overview.
 *
 * Reutiliza el panel existente sin duplicar lógica (regla del owner).
 */
const CreatorChannels = () => {
  const { botId } = useParams();
  const navigate = useNavigate();

  const [bot, setBot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      if (!botId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await botService.get(botId);
        setBot(res.data);
      } catch (err) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Error cargando el bot');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [botId]);

  const handleClose = () => {
    navigate(`/bots/${botId}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <CreatorError
        title="No se pudo cargar el bot"
        description={error}
        ctaLabel="Reintentar"
        onCta={() => window.location.reload()}
        secondaryLabel="Volver al inicio"
        onSecondary={() => navigate(`/bots/${botId}`)}
      />
    );
  }

  return (
    <>
      <div className="text-center text-white/50 text-sm py-8">
        Cargando canales...
      </div>
      <ChannelsPanel
        open={true}
        bot={bot}
        onClose={handleClose}
      />
    </>
  );
};

export default CreatorChannels;
