import { apiClient } from "../api/apiClient";
import type { LoginCredentials, LoginResponse, UserSession } from "../../types/auth";

async function login(credentials: LoginCredentials): Promise<UserSession> {
  const response = await apiClient.request<LoginResponse>("/login", {
    method: "POST",
    body: credentials
  });

  return {
    token: response.data.token.access_token,
    user: response.data.user
  };
}

export const authService = {
  login
};
