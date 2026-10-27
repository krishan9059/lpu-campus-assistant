import { Navigate, Route, Routes } from "react-router-dom";

import { RequireAuth, RequireRole } from "@/components/RequireRole";
import { AdminPage } from "@/pages/AdminPage";
import { ChatPage } from "@/pages/ChatPage";
import { HomePage } from "@/pages/HomePage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { PlacementPage } from "@/pages/PlacementPage";
import { SignInPage } from "@/pages/SignInPage";

export function App() {
  return (
    <Routes>
      <Route path="/sign-in" element={<SignInPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <HomePage />
          </RequireAuth>
        }
      />
      <Route
        path="/chat/:assistantId"
        element={
          <RequireAuth>
            <ChatPage />
          </RequireAuth>
        }
      />
      <Route
        path="/placement"
        element={
          <RequireAuth>
            <PlacementPage />
          </RequireAuth>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireRole role="admin">
            <AdminPage />
          </RequireRole>
        }
      />
      <Route path="/404" element={<NotFoundPage />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}
