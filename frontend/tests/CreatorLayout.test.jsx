import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import CreatorLayout from '../src/components/creator/CreatorLayout';

const renderLayout = (botName = 'Mi Bot') =>
  render(
    <MemoryRouter initialEntries={['/bots/1']}>
      <Routes>
        <Route
          path="/bots/:botId"
          element={<CreatorLayout botName={botName} botStatus="ready" />}
        >
          <Route index element={<div>CONTENIDO OUTLET</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );

describe('CreatorLayout', () => {
  it('renderiza el nombre del bot', () => {
    renderLayout('Mi Bot Test');
    const matches = screen.getAllByText(/Mi Bot Test/i);
    expect(matches.length).toBeGreaterThan(0);
  });

  it('renderiza el Outlet (contenido hijo)', () => {
    renderLayout();
    expect(screen.getByText('CONTENIDO OUTLET')).toBeInTheDocument();
  });

  it('muestra badge de estado "Listo"', () => {
    renderLayout();
    const matches = screen.getAllByText(/Listo/i);
    expect(matches.length).toBeGreaterThan(0);
  });
});
