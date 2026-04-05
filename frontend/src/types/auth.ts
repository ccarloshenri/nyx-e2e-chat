export type AuthUser = {
  user_id: string;
  username: string;
  public_key?: string;
  encrypted_private_key?: string;
  kdf_salt?: string;
  kdf_params?: Record<string, unknown>;
};

export type UserSession = {
  token: string;
  user: AuthUser;
};

export type LoginCredentials = {
  username: string;
  password: string;
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
  logout: () => void;
};
