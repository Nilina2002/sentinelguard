import { useState } from "react";
import api from "../api/client";
import { useNavigate } from "react-router-dom";
import Loading from "../components/Loading";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const handleRegister = async () => {
    setLoading(true);
    try {
      const res = await api.post("/auth/register", { email, password });
      if (!res.data.success) throw new Error(res.data.message || "Registration failed");

      const userRes = await api.get("/users/me");
      setUser(userRes.data);

      toast.success("Registered successfully");
      navigate("/home");
    } catch (err: any) {
      toast.error(`Registration failed: ${err.response?.data?.message || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading message="Registering..." />;

  return (
    <div className="flex items-center justify-center h-screen bg-gray-100">
      <div className="bg-white p-6 rounded-lg shadow-md w-80">
        <h2 className="text-xl font-bold mb-4">Register</h2>

        <input
          className="w-full border p-2 mb-3 rounded"
          placeholder="Email"
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          className="w-full border p-2 mb-3 rounded"
          placeholder="Password"
          onChange={(e) => setPassword(e.target.value)}
        />

        <button
          onClick={handleRegister}
          className="w-full bg-green-500 text-white p-2 rounded"
        >
          Register
        </button>

        <button
          onClick={() => navigate("/login")}
          className="w-full bg-blue-800 text-white p-2 rounded mt-2"
        >
          Login
        </button>
      </div>
    </div>
  );
}
