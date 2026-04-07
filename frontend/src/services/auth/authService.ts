import { apiClient } from "../api/apiClient";
import type {
  LoginCredentials,
  LoginResponse,
  RegisterCredentials,
  RegisterPayload,
  RegisterResponse,
  UserSession,
} from "../../types/auth";
import { createCryptoService } from "../crypto/cryptoService";

const cryptoService = createCryptoService();

async function login(credentials: LoginCredentials): Promise<UserSession> {
  const response = await apiClient.request<LoginResponse>("/auth/login", {
    method: "POST",
    body: credentials
  });

  return {
    token: response.data.token.access_token,
    user: response.data.user
  };
}

async function register(credentials: RegisterCredentials): Promise<void> {
  const keyMaterial = await cryptoService.buildRegistrationKeyMaterial(credentials.password);
  const payload: RegisterPayload = {
    username: credentials.username,
    password: credentials.password,
    ...keyMaterial,
  };

  await apiClient.request<RegisterResponse>("/auth/register", {
    method: "POST",
    body: payload,
  });
}

export const authService = {
  login,
  register,
};
