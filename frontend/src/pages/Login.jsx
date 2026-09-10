import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { botService } from '../services/api';
import Button from '../components/Button';
import Card from '../components/Card';
import Input from '../components/Input';
import Badge from '../components/Badge';

const LOGO_URL = '/logo.png';

const Login = () => {
  const navigate = useNavigate();
  const { login, register } = useAuth();

  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
        // Redirigir al dashboard después del login
        navigate('/dashboard');
      } else {
        // Registro
        await register({ email, password, full_name: fullName });
        // Hacer login automático después del registro
        await login(email, password);
        // Redirigir al onboarding (nuevo usuario)
        navigate('/onboarding');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error de autenticación');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-navy flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 bg-navy/80 border-white/10 shadow-glow">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <img src={LOGO_URL} alt="Nuvora" className="h-12 w-12 rounded-xl object-cover" />
            <span className="text-2xl font-bold">Nuvora</span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            {isLogin ? 'Inicia sesión' : 'Crea tu cuenta'}
          </h1>
          <p className="text-white/50 text-sm mt-1">
            {isLogin ? 'Accede a tu dashboard' : 'Empieza tu prueba gratuita de 30 días'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <Input
              label="Nombre completo"
              placeholder="Tu nombre"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required={!isLogin}
            />
          )}

          <Input
            label="Email"
            type="email"
            placeholder="tu@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <Input
            label="Contraseña"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            disabled={loading}
          >
            {loading ? 'Cargando...' : (isLogin ? 'Iniciar sesión' : 'Registrarse gratis')}
          </Button>
        </form>

        <p className="text-center text-white/40 text-sm mt-6">
          {isLogin ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?'}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-cyan-400 hover:underline ml-1"
          >
            {isLogin ? 'Regístrate gratis' : 'Inicia sesión'}
          </button>
        </p>

        <div className="mt-6 pt-6 border-t border-white/5 text-center">
          <Badge variant="trial">30 días de prueba gratis</Badge>
        </div>
      </Card>
    </div>
  );
};

export default Login;
