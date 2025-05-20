'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Eye, EyeOff } from 'lucide-react';
import { useRouter } from 'next/navigation';

export function RegisterForm() {
  const { register, isLoading, error: authError } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [registrationComplete, setRegistrationComplete] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    
    if (password !== passwordConfirm) {
      setFormError("Passwords do not match");
      return;
    }
    
    try {
      const response = await register({ 
        username, 
        email, 
        phone,
        password,
        password_confirm: passwordConfirm 
      });
      setRegistrationComplete(true);
      return response;
    } catch (err) {
      console.error('Registration error:', err);
      setFormError(err instanceof Error ? err.message : 'Registration failed');
    }
  };
 
  const togglePasswordVisibility = () => setShowPassword(!showPassword);
  const togglePasswordConfirmVisibility = () => setShowPasswordConfirm(!showPasswordConfirm);
  const error = formError || authError;

  if (registrationComplete) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <CardTitle>Registration Successful</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center">
            <p className="text-green-600 mb-4">
              Your account has been created successfully!
            </p>
            <Button
              className="mt-4"
              onClick={() => router.push('/login')}
            >
              Proceed to Login
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Create an Account</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <ErrorAlert 
              error={error} 
              onDismiss={() => setFormError(null)}
            />
          )}
          
          <div className="space-y-2">
            <label htmlFor="username" className="text-sm font-medium">Username</label>
            <Input
              id="username"
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">Email</label>
            <Input
              id="email"
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="phone" className="text-sm font-medium">Phone Number</label>
            <Input
              id="phone"
              type="tel"
              placeholder="Phone Number"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>

          <div className="space-y-2 relative">
            <label htmlFor="password" className="text-sm font-medium">Password</label>
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              required
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-2 top-9"
              onClick={togglePasswordVisibility}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </Button>
          </div>

          <div className="space-y-2 relative">
            <label htmlFor="passwordConfirm" className="text-sm font-medium">Confirm Password</label>
            <Input
              id="passwordConfirm"
              type={showPasswordConfirm ? "text" : "password"}
              placeholder="Confirm Password"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              disabled={isLoading}
              required
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-2 top-9"
              onClick={togglePasswordConfirmVisibility}
            >
              {showPasswordConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
            </Button>
          </div>

          <Button 
            type="submit" 
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? 'Creating account...' : 'Register'}
          </Button>

          <div className="text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link href="/login" className="text-blue-600 hover:underline">
              Login
            </Link>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
