import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import CreatorError from '../../components/creator/CreatorError';
import Spinner from '../../components/ui/Spinner';
import BotOverviewCard from '../../components/creator/BotOverviewCard';
import BotReadiness from '../../components/creator/BotReadiness';
import SetupChecklist from '../../components/creator/SetupChecklist';
import NextStepCard from '../../components/creator/NextStepCard';
import { useCreatorStatus } from '../../hooks/useCreatorStatus';
import { botService } from '../../services/api';
import { getNicho } from '../../data/nichos';

/**
 * CreatorOverview — Página inicial del Creator Workspace.
 *
 * Carga:
 *   - bot desde GET /bots/{id}
 *   - creator status desde GET /bots/{id}/creator-status
 *
 * Compone:
 *   - BotOverviewCard   (nombre + nicho + estado)
 *   - NextStepCard      (siguiente paso determinista)
 *   - BotReadiness      (READY = config + workflow + publication)
 *   - SetupChecklist    (checklist de pasos)
 */
const CreatorOverview = () => {
  const { botId } = useParams();
  const navigate = useNavigate();
  const { status, loading: statusLoading, error: statusError, reload } = useCreatorStatus(botId);

  const [bot, setBot] = useState(null);
  const [botLoading, setBotLoading] = useState(true);
  const [botError, setBotError] = useState(null);

  useEffect(() => {
    const loadBot = async () => {
      if (!botId) return;
      setBotLoading(true);
      setBotError(null);
      try {
        const res = await botService.get(botId);
        setBot(res.data);
      } catch (err) {
        const detail = err.response?.data?.detail;
        setBotError(typeof detail === 'string' ? detail : 'Error cargando el bot');
      } finally {
        setBotLoading(false);
      }
    };
    loadBot();
  }, [botId]);

  const handleGoTo = (section) => {
    if (!section) return;
    navigate(`/bots/${botId}/${section}`);
  };

  const handleRetry = () => {
    reload();
    setBotError(null);
  };

  // ----- Loading -----
  if (botLoading || statusLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner />
      </div>
    );
  }

  // ----- Error del bot -----
  if (botError) {
    return (
      <CreatorError
        title="No se pudo cargar el bot"
        description={botError}
        ctaLabel="Reintentar"
        onCta={handleRetry}
        secondaryLabel="Volver a Mis bots"
        onSecondary={() => navigate('/dashboard')}
      />
    );
  }

  // ----- Error del status -----
  if (statusError) {
    return (
      <CreatorError
        title="No se pudo cargar el estado del bot"
        description={statusError}
        ctaLabel="Reintentar"
        onCta={handleRetry}
        secondaryLabel="Volver a Mis bots"
        onSecondary={() => navigate('/dashboard')}
      />
    );
  }

  if (!bot) {
    return (
      <CreatorError
        title="Bot no encontrado"
        description="El bot que buscas no existe o no tienes acceso a él."
        secondaryLabel="Volver a Mis bots"
        onSecondary={() => navigate('/dashboard')}
      />
    );
  }

  const nicho = getNicho(bot.nicho_id);

  return (
    <div className="space-y-5">
      {/* Card principal */}
      <BotOverviewCard
        bot={bot}
        status={status}
        nichoName={nicho?.name}
      />

      {/* Siguiente paso */}
      <NextStepCard
        nextStep={status?.next_step}
        onGoTo={handleGoTo}
      />

      {/* Grid de 2 columnas en desktop */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <BotReadiness
          status={status}
          onGoTo={handleGoTo}
        />
        <SetupChecklist
          status={status}
          onGoTo={handleGoTo}
        />
      </div>
    </div>
  );
};

export default CreatorOverview;
