import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { AuthCardLayout } from "../../components/layout/AuthCardLayout";
import { Button } from "../../components/ui/Button";
import { InputField } from "../../components/ui/InputField";
import { useAuth } from "../../hooks/useAuth";

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, isAuthenticated } = useAuth();
  const [username, setUsername] = useState("");
  const [masterPassword, setMasterPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/conversations" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    if (masterPassword !== confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);

    try {
      await register({ username, masterPassword, confirmPassword });
      navigate("/conversations", { replace: true });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to create account.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthCardLayout
      eyebrow="Private onboarding"
      title="Create your Nyx account"
      description="Create a master password that stays on the client and protects your local conversation secrets."
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <InputField
          id="register-username"
          label="Username"
          placeholder="alice"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
          required
          minLength={3}
        />
        <InputField
          id="register-password"
          label="Master password"
          type="password"
          placeholder="Create a strong master password"
          value={masterPassword}
          onChange={(event) => setMasterPassword(event.target.value)}
          autoComplete="new-password"
          required
          minLength={8}
        />
        <InputField
          id="register-confirm-password"
          label="Confirm master password"
          type="password"
          placeholder="Repeat your password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          autoComplete="new-password"
          required
          minLength={8}
        />
        {errorMessage ? <div className="banner-error">{errorMessage}</div> : null}
        <Button type="submit" fullWidth disabled={isSubmitting}>
          {isSubmitting ? "Creating account..." : "Create account"}
        </Button>
        <p className="auth-support-text">
          Already have an account? <Link to="/login" className="auth-inline-link">Sign in</Link>
        </p>
      </form>
    </AuthCardLayout>
  );
}
