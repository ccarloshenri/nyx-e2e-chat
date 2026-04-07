export type AuthUser = {
  user_id: string;
  username: string;
  public_key?: string;
  encrypted_private_key?: string;
  secret_wrap_salt?: string;
  secret_wrap_kdf_params?: Record<string, unknown>;
  private_key_wrap_salt?: string;
  private_key_wrap_kdf_params?: Record<string, unknown>;
};

export type UserSession = {
  token: string;
  user: AuthUser;
};

export type LoginCredentials = {
  username: string;
  masterPassword: string;
};

export type RegisterCredentials = LoginCredentials & {
  confirmPassword?: string;
};

export type RegisterPayload = {
  username: string;
  master_password_verifier: string;
  master_password_salt: string;
  master_password_kdf_params: Record<string, unknown>;
  secret_wrap_salt: string;
  secret_wrap_kdf_params: Record<string, unknown>;
  public_key: string;
  encrypted_private_key: string;
  private_key_wrap_salt: string;
  private_key_wrap_kdf_params: Record<string, unknown>;
};

export type RegisterResponse = {
  success: boolean;
  data: {
    user_id: string;
    username: string;
    created_at: string;
  };
};

export type LoginChallengeResponse = {
  success: boolean;
  data: {
    challenge_token: string;
    master_password_salt: string;
    master_password_kdf_params: Record<string, unknown>;
    expires_at: string;
  };
};

export type LoginResponse = {
  success: boolean;
  data: {
    token: {
      access_token: string;
      expires_at: string;
    };
    user: AuthUser;
  };
};

export type AuthContextValue = {
  session: UserSession | null;
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isRestoring: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
};
