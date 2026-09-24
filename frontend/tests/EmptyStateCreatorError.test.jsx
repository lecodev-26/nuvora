import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import EmptyState from '../src/components/creator/EmptyState';
import CreatorError from '../src/components/creator/CreatorError';

describe('EmptyState', () => {
  it('renderiza título + descripción + CTA', () => {
    const onCta = vi.fn();
    render(
      <EmptyState
        icon="📭"
        title="Nada aquí"
        description="Añade algo"
        ctaLabel="Añadir"
        onCta={onCta}
      />
    );
    expect(screen.getByText('Nada aquí')).toBeInTheDocument();
    expect(screen.getByText('Añade algo')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Añadir' }));
    expect(onCta).toHaveBeenCalled();
  });
});

describe('CreatorError', () => {
  it('renderiza título + descripción', () => {
    render(<CreatorError title="Error X" description="Algo falló" />);
    expect(screen.getByText('Error X')).toBeInTheDocument();
    expect(screen.getByText('Algo falló')).toBeInTheDocument();
  });

  it('renderiza dos botones si hay secondary', () => {
    render(
      <CreatorError
        title="Error"
        ctaLabel="Reintentar"
        onCta={vi.fn()}
        secondaryLabel="Volver"
        onSecondary={vi.fn()}
      />
    );
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Volver' })).toBeInTheDocument();
  });
});
