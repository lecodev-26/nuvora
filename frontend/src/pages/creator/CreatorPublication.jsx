import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import PublicationPanel from '../../components/publication/PublicationPanel';

/**
 * CreatorPublication — Página de Publicación dentro de Creator Mode.
 *
 * Monta el PublicationPanel existente (modal) abierto por defecto.
 * Al cerrar → vuelve al Overview.
 *
 * Reutiliza el panel existente sin duplicar lógica.
 */
const CreatorPublication = () => {
  const { botId } = useParams();
  const navigate = useNavigate();

  const handleClose = () => {
    navigate(`/bots/${botId}`);
  };

  const handlePublished = () => {
    // Opcional: refrescar status o hacer algo al publicar
    // Por ahora, no-op (el panel se encarga de la UI)
  };

  return (
    <>
      <div className="text-center text-white/50 text-sm py-8">
        Cargando publicación...
      </div>
      <PublicationPanel
        open={true}
        botId={parseInt(botId)}
        onClose={handleClose}
        onPublished={handlePublished}
      />
    </>
  );
};

export default CreatorPublication;
