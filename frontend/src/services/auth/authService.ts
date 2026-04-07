import { apiClient } from "../api/apiClient";
import type {
  LoginChallengeResponse,
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
  const challengeResponse = await apiClient.request<LoginChallengeResponse>("/auth/challenge", {
    method: "POST",
    body: { username: credentials.username },
  });

  const loginProof = await cryptoService.createLoginProof(
    credentials.masterPassword,
    challengeResponse.data.challenge_token,
    challengeResponse.data.master_password_salt,
    challengeResponse.data.master_password_kdf_params,
  );

  const response = await apiClient.request<LoginResponse>("/auth/login", {
    method: "POST",
    body: {
      username: credentials.username,
      challenge_token: challengeResponse.data.challenge_token,
      login_proof: loginProof,
    },
  });

  return {
    token: response.data.token.access_token,
    user: response.data.user,
  };
}

async function register(credentials: RegisterCredentials): Promise<void> {
  const registrationMaterial = await cryptoService.buildAccountRegistration(credentials.masterPassword);
  const payload: RegisterPayload = {
    username: credentials.username,
    ...registrationMaterial,
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
