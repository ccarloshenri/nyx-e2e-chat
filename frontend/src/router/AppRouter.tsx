import { Navigate, Route, Routes } from "react-router-dom";
import { ConversationsPage } from "../pages/conversations/ConversationsPage";
import { LoginPage } from "../pages/login/LoginPage";
import { ProtectedRoute } from "./ProtectedRoute";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/conversations" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/conversations"
        element={
          <ProtectedRoute>
            <ConversationsPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
