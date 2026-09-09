import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register({ email, password, full_name: fullName });
        // Después de registrar, hacer login automático
        await login(email, password);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error de autenticación');
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A14] flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.07] to-white/[0.02] backdrop-blur-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-[#00C6FF] to-[#FF4ECD] bg-clip-text text-transparent">
            Nuvora
          </h1>
          <p className="text-white/50 text-sm mt-2">
            {isLogin ? 'Inicia sesión en tu cuenta' : 'Crea tu cuenta gratis'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="text-xs text-white/70 block mb-1">Nombre completo</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-white/[0.06] border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-[#7B5CFF] text-white"
                placeholder="Tu nombre"
                required={!isLogin}
              />
            </div>
          )}
          <div>
            <label className="text-xs text-white/70 block mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-white/[0.06] border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-[#7B5CFF] text-white"
              placeholder="tu@email.com"
              required
            />
          </div>
          <div>
            <label className="text-xs text-white/70 block mb-1">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white/[0.06] border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-[#7B5CFF] text-white"
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full rounded-xl py-3.5 font-semibold bg-gradient-to-r from-[#00C6FF] to-[#FF4ECD] hover:opacity-90 transition shadow-[0_0_20px_rgba(123,92,255,0.4)]"
          >
            {isLogin ? 'Iniciar sesión' : 'Registrarse'}
          </button>
        </form>

        <p className="text-center text-white/40 text-sm mt-6">
          {isLogin ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?'}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-[#00C6FF] hover:underline ml-1"
          >
            {isLogin ? 'Regístrate' : 'Inicia sesión'}
          </button>
        </p>
      </div>
    </div>
  );
};

export default Login;
