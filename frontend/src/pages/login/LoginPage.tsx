import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { AuthCardLayout } from "../../components/layout/AuthCardLayout";
import { Button } from "../../components/ui/Button";
import { InputField } from "../../components/ui/InputField";
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
      <form className="auth-form" onSubmit={handleSubmit}>
        <InputField
          id="username"
          label="Username"
          placeholder="carlo"
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
        <p className="auth-support-text">
          Need an account? <Link to="/register" className="auth-inline-link">Create one</Link>
        </p>
      </form>
    </AuthCardLayout>
  );
}
