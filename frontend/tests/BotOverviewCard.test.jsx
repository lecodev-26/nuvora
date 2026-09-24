import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

import BotOverviewCard from '../src/components/creator/BotOverviewCard';

const BOT = { id: 1, name: 'Mi Bot', description: 'Un bot de prueba', business_name: 'Test SA' };

describe('BotOverviewCard', () => {
  it('renderiza el nombre', () => {
    render(<BotOverviewCard bot={BOT} />);
    expect(screen.getByText('Mi Bot')).toBeInTheDocument();
  });

  it('renderiza la descripción', () => {
    render(<BotOverviewCard bot={BOT} />);
    expect(screen.getByText('Un bot de prueba')).toBeInTheDocument();
  });

  it('badge "Listo" si status.ready=true', () => {
    render(<BotOverviewCard bot={BOT} status={{ ready: true }} />);
    expect(screen.getByText(/Listo/i)).toBeInTheDocument();
  });

  it('badge "En construcción" si status.ready=false', () => {
    render(<BotOverviewCard bot={BOT} status={{ ready: false }} />);
    expect(screen.getByText(/En construcción/i)).toBeInTheDocument();
  });

  it('no renderiza si bot=null', () => {
    const { container } = render(<BotOverviewCard bot={null} />);
    expect(container.firstChild).toBeNull();
  });
});
