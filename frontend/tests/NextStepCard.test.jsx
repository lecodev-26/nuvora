import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import NextStepCard from '../src/components/creator/NextStepCard';

describe('NextStepCard', () => {
  it('next_step="workflow" → CTA Ir a Flujos', () => {
    const onGoTo = vi.fn();
    render(<NextStepCard nextStep="workflow" onGoTo={onGoTo} />);
    expect(screen.getByText(/Crea o activa un workflow/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Ir a Flujos/i }));
    expect(onGoTo).toHaveBeenCalledWith('workflows');
  });

  it('next_step="publication" → CTA Publicar bot', () => {
    render(<NextStepCard nextStep="publication" />);
    expect(screen.getByText(/Publica tu bot/i)).toBeInTheDocument();
  });

  it('next_step=null → mensaje de éxito', () => {
    render(<NextStepCard nextStep={null} />);
    expect(screen.getByText(/Tu bot está funcionando/i)).toBeInTheDocument();
  });
});
