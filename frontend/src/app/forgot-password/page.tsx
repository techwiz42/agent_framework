'use client';
import { useState } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { authService } from '@/services/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const { toast } = useToast();

  const handlePasswordResetRequest = async () => {
    // Validate email
    if (!email || !email.includes('@')) {
      toast({
        title: "Invalid Email",
        description: "Please enter a valid email address",
        variant: "destructive"
      });
      return;
    }

    try {
      await authService.requestPasswordReset(email);
      
      toast({
        title: "Reset Link Sent",
        description: "Password reset link has been sent to your email",
        variant: "default"
      });
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : "Failed to send reset link";
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10">
      <h2 className="text-2xl mb-4">Reset Password</h2>
      <Input 
        type="email"
        placeholder="Enter your email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="mb-4"
        required
      />
      <Button onClick={handlePasswordResetRequest}>
        Send Reset Link
      </Button>
    </div>
  );
}
