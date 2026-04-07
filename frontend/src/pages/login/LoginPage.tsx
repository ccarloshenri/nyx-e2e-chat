import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { AuthCardLayout } from "../../components/layout/AuthCardLayout";
import { Button } from "../../components/ui/Button";
import { InputField } from "../../components/ui/InputField";
import { Logo } from "../../components/ui/Logo";
import { useAuth } from "../../hooks/useAuth";

type LocationState = {
  from?: string;
};

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const state = location.state as LocationState | null;
  const redirectTo = state?.from ?? "/conversations";

  if (isAuthenticated) {
    return <Navigate to="/conversations" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await login({ username, password });
      navigate(redirectTo, { replace: true });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthCardLayout
      eyebrow="End-to-end secure"
      title="Welcome back to Nyx"
      description="Authenticate to restore your protected session and continue your private conversations."
    >
      <div className="auth-logo-wrap">
        <Logo size={80} className="nyx-logo auth-logo" />
      </div>
      <form className="auth-form" onSubmit={handleSubmit}>
        <InputField
          id="username"
          label="Email or username"
          placeholder="carlo@nyx.app"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
          required
        />
        <InputField
          id="password"
          label="Password"
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />
        {errorMessage ? <div className="banner-error">{errorMessage}</div> : null}
        <Button type="submit" fullWidth disabled={isSubmitting}>
          {isSubmitting ? "Signing in..." : "Sign in"}
        </Button>
      </form>
    </AuthCardLayout>
  );
}
