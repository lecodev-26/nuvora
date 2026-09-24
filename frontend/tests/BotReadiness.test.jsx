import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import BotReadiness from '../src/components/creator/BotReadiness';

describe('BotReadiness', () => {
  it('muestra los 3 items', () => {
    const status = {
      configuration: { ok: true },
      workflow: { ok: false },
      publication: { ok: false },
      ready: false,
    };
    render(<BotReadiness status={status} />);
    expect(screen.getByText(/Configuración/i)).toBeInTheDocument();
    expect(screen.getByText(/Workflow activo/i)).toBeInTheDocument();
    expect(screen.getByText(/Publicado/i)).toBeInTheDocument();
  });

  it('muestra progreso correcto', () => {
    const status = {
      configuration: { ok: true },
      workflow: { ok: true },
      publication: { ok: false },
      ready: false,
    };
    render(<BotReadiness status={status} />);
    expect(screen.getByText(/2 de 3/i)).toBeInTheDocument();
  });

  it('CTA navega cuando hay onGoTo', () => {
    const onGoTo = vi.fn();
    const status = {
      configuration: { ok: false },
      workflow: { ok: false },
      publication: { ok: false },
      ready: false,
    };
    render(<BotReadiness status={status} onGoTo={onGoTo} />);
    const btn = screen.getByRole('button', { name: /Ir a Configuración/i });
    fireEvent.click(btn);
    expect(onGoTo).toHaveBeenCalledWith('config');
  });
});
