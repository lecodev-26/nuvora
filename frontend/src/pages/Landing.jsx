import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';

const LOGO_URL = '/logo.png';

const Landing = () => {
  const [isDark, setIsDark] = useState(true);

  // Alternar modo oscuro/claro
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  return (
    <div className="min-h-screen bg-navy text-white overflow-x-hidden">
      {/* ============================================================
          HEADER / NAV
          ============================================================ */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-navy/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img src={LOGO_URL} alt="Nuvora" className="h-10 w-10 rounded-xl object-cover" />
            <span className="text-xl font-bold">Nuvora</span>
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-sm text-white/70">
            <a href="#como-funciona" className="hover:text-white transition">Cómo funciona</a>
            <a href="#beneficios" className="hover:text-white transition">Beneficios</a>
            <a href="#precio" className="hover:text-white transition">Precio</a>
            <Link to="/login" className="hover:text-white transition">Iniciar sesión</Link>
          </nav>

          <div className="flex items-center gap-3">
            {/* Toggle modo oscuro/claro */}
            <button
              onClick={() => setIsDark(!isDark)}
              className="p-2 rounded-full bg-white/5 hover:bg-white/10 transition text-white/70 hover:text-white"
              aria-label="Alternar modo"
            >
              {isDark ? '☀️' : '🌙'}
            </button>
            <Link to="/login">
              <Button variant="primary" size="sm">Probar gratis</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* ============================================================
          HERO
          ============================================================ */}
      <section className="pt-32 pb-20 px-4 md:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Texto */}
          <div className="space-y-6 animate-fade-in-up">
            <Badge variant="cyan" className="mb-2">🤖 Asistente inteligente</Badge>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold leading-tight">
              El asistente inteligente
              <br />
              <span className="text-gradient">para tu negocio</span>
            </h1>
            <p className="text-lg md:text-xl text-white/60 max-w-lg leading-relaxed">
              Responde automáticamente a las preguntas de tus clientes usando
              la información de tu propio negocio. Sin complicaciones, sin esperas.
            </p>
            <div className="flex flex-wrap gap-4 pt-2">
              <Link to="/login">
                <Button variant="primary" size="lg" className="animate-pulse-glow">
                  Probar gratis
                </Button>
              </Link>
              <a href="#como-funciona">
                <Button variant="secondary" size="lg">
                  Ver cómo funciona
                </Button>
              </a>
            </div>
            <p className="text-sm text-white/40">✓ Sin tarjeta de crédito · 30 días de prueba</p>
          </div>

          {/* Demo del widget */}
          <div className="relative flex justify-center">
            <div className="w-full max-w-sm">
              <Card className="p-0 overflow-hidden border-white/20 shadow-glow bg-gradient-hero">
                {/* Header del widget demo */}
                <div className="bg-gradient-primary p-4 flex items-center gap-3">
                  <img src={LOGO_URL} alt="Nuvora" className="h-8 w-8 rounded-lg object-cover" />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-white">Nuvora Bot</p>
                    <p className="text-xs text-white/70 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      En línea
                    </p>
                  </div>
                  <span className="text-white/50 text-sm">✕</span>
                </div>

                {/* Mensajes del widget demo */}
                <div className="p-4 space-y-3 bg-navy/50 min-h-[260px]">
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-gradient-primary flex items-center justify-center text-xs font-bold text-white flex-shrink-0">N</div>
                    <div className="bg-white/10 rounded-2xl rounded-tl-none px-4 py-2.5 text-sm max-w-[80%]">
                      ¡Hola! Soy el asistente de <span className="font-semibold text-white">Restaurante La Marina</span>. ¿En qué puedo ayudarte?
                    </div>
                  </div>

                  {/* Sugerencias rápidas */}
                  <div className="flex flex-wrap gap-2 ml-9">
                    <span className="px-3 py-1.5 text-xs rounded-full bg-violet-500/20 text-violet-400 border border-violet-500/30 cursor-pointer hover:bg-violet-500/30 transition">Horario</span>
                    <span className="px-3 py-1.5 text-xs rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 cursor-pointer hover:bg-cyan-500/30 transition">Menú</span>
                    <span className="px-3 py-1.5 text-xs rounded-full bg-magenta-500/20 text-magenta-400 border border-magenta-500/30 cursor-pointer hover:bg-magenta-500/30 transition">Reservas</span>
                  </div>

                  {/* Mensaje del usuario */}
                  <div className="flex justify-end">
                    <div className="bg-gradient-primary rounded-2xl rounded-tr-none px-4 py-2.5 text-sm max-w-[80%] text-white">
                      ¿A qué hora abrís?
                    </div>
                  </div>

                  {/* Respuesta del bot */}
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-gradient-primary flex items-center justify-center text-xs font-bold text-white flex-shrink-0">N</div>
                    <div className="bg-white/10 rounded-2xl rounded-tl-none px-4 py-2.5 text-sm max-w-[80%]">
                      Abrimos de <span className="text-cyan-400 font-medium">9:00 a 18:00</span>, de lunes a domingo. ¿Quieres reservar una mesa?
                    </div>
                  </div>

                  {/* Input simulado */}
                  <div className="flex items-center gap-2 mt-2 pt-2 border-t border-white/5">
                    <div className="flex-1 bg-white/5 rounded-full px-4 py-2 text-sm text-white/30">Escribe tu pregunta...</div>
                    <div className="p-2 rounded-full bg-gradient-primary text-white text-sm font-bold">→</div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Glow de fondo */}
            <div className="absolute -inset-10 bg-gradient-primary opacity-20 blur-3xl -z-10" />
          </div>
        </div>
      </section>

      {/* ============================================================
          CÓMO FUNCIONA
          ============================================================ */}
      <section id="como-funciona" className="py-20 px-4 md:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <Badge variant="cyan" className="mb-4">Cómo funciona</Badge>
          <h2 className="text-3xl md:text-4xl font-bold">Configura tu asistente en <span className="text-gradient">4 pasos</span></h2>
          <p className="text-white/50 mt-4">Sin complicaciones, sin necesidad de saber programar.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { step: '01', title: 'Crea tu negocio', desc: 'Registra tu cuenta y configura los datos de tu negocio.' },
            { step: '02', title: 'Añade tu información', desc: 'Incluye la información que quieras que conozca tu asistente.' },
            { step: '03', title: 'Prueba tu asistente', desc: 'Haz una prueba y comprueba cómo responde.' },
            { step: '04', title: 'Instala en tu web', desc: 'Copia el código y añade el widget a tu sitio web.' },
          ].map((item, index) => (
            <Card key={index} className="text-center hover:border-violet-500/30 transition-all duration-300 group">
              <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-primary opacity-30 group-hover:opacity-100 transition">
                {item.step}
              </div>
              <h3 className="text-lg font-semibold mt-3">{item.title}</h3>
              <p className="text-sm text-white/50 mt-1">{item.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* ============================================================
          BENEFICIOS
          ============================================================ */}
      <section id="beneficios" className="py-20 px-4 md:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <Badge variant="magenta" className="mb-4">Beneficios</Badge>
          <h2 className="text-3xl md:text-4xl font-bold">Más que un chatbot, un <span className="text-gradient">asistente para tu negocio</span></h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { icon: '⚡', title: 'Responde automáticamente', desc: 'Tus clientes obtienen respuestas al instante, sin esperar.' },
            { icon: '🧠', title: 'Basado en tu información', desc: 'Nuvora utiliza la información que proporciona cada negocio.' },
            { icon: '🕐', title: 'Disponible siempre', desc: 'Tu asistente puede atender preguntas aunque el negocio esté cerrado.' },
            { icon: '📦', title: 'Fácil de instalar', desc: 'Puedes añadirlo a tu web sin necesidad de crear un sistema desde cero.' },
          ].map((item, index) => (
            <Card key={index} className="text-center hover:border-cyan-500/30 transition-all duration-300">
              <div className="text-4xl mb-3">{item.icon}</div>
              <h3 className="text-lg font-semibold">{item.title}</h3>
              <p className="text-sm text-white/50 mt-1">{item.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* ============================================================
          PRECIO
          ============================================================ */}
      <section id="precio" className="py-20 px-4 md:px-8 max-w-4xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <Badge variant="primary" className="mb-4">Precio simple y transparente</Badge>
          <h2 className="text-3xl md:text-4xl font-bold">Todo lo que necesitas, <span className="text-gradient">por un solo pago</span></h2>
        </div>

        <Card className="text-center p-8 md:p-12 border-2 border-violet-500/20 shadow-glow bg-gradient-hero relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-primary opacity-10 blur-3xl -z-10" />

          <Badge variant="cyan" className="mb-4">Plan único</Badge>
          <div className="text-5xl md:text-6xl font-extrabold">29,99 €</div>
          <p className="text-white/50 text-lg mt-2">/ 12 meses</p>

          <div className="max-w-sm mx-auto my-6 space-y-2 text-sm text-white/70">
            <p className="flex items-center justify-center gap-2">
              <span className="text-emerald-400">✓</span> Sin renovación automática
            </p>
            <p className="flex items-center justify-center gap-2">
              <span className="text-emerald-400">✓</span> Pagas una vez y disfrutas de Nuvora durante 12 meses
            </p>
            <p className="flex items-center justify-center gap-2">
              <span className="text-emerald-400">✓</span> 1 bot · Actualizaciones · Soporte por email
            </p>
          </div>

          <Link to="/login">
            <Button variant="primary" size="lg" className="animate-pulse-glow">
              Probar gratis
            </Button>
          </Link>
          <p className="text-xs text-white/30 mt-3">30 días de prueba · Sin tarjeta de crédito</p>
        </Card>
      </section>

      {/* ============================================================
          FOOTER
          ============================================================ */}
      <footer className="border-t border-white/5 py-12 px-4 md:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <img src={LOGO_URL} alt="Nuvora" className="h-8 w-8 rounded-lg object-cover" />
              <span className="text-lg font-bold">Nuvora</span>
            </div>
            <p className="text-sm text-white/40 max-w-xs">
              El asistente inteligente para tu negocio.
            </p>
          </div>
          <div>
            <h4 className="text-sm font-semibold mb-3">Producto</h4>
            <ul className="space-y-2 text-sm text-white/40">
              <li><a href="#como-funciona" className="hover:text-white transition">Cómo funciona</a></li>
              <li><a href="#precio" className="hover:text-white transition">Precio</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold mb-3">Empresa</h4>
            <ul className="space-y-2 text-sm text-white/40">
              <li><a href="#" className="hover:text-white transition">Contacto</a></li>
              <li><a href="#" className="hover:text-white transition">Términos de servicio</a></li>
              <li><a href="#" className="hover:text-white transition">Privacidad</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold mb-3">Legal</h4>
            <ul className="space-y-2 text-sm text-white/40">
              <li><a href="#" className="hover:text-white transition">Política de cookies</a></li>
              <li><a href="#" className="hover:text-white transition">Aviso legal</a></li>
            </ul>
          </div>
        </div>
        <div className="mt-12 pt-6 border-t border-white/5 text-center text-sm text-white/30">
          © 2026 Nuvora. Todos los derechos reservados.
        </div>
      </footer>
    </div>
  );
};

export default Landing;
