import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Loading from "../components/Loading";

export default function RootRedirect() {
  const { user, loading } = useAuth();

  if (loading) return <Loading message="Loading…" fullScreen />;

  return user ? <Navigate to="/home" replace /> : <Navigate to="/login" replace />;
}
