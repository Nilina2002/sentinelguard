import { Link, useNavigate } from "react-router-dom";
import api from "../../api/client";
import { useAuth } from "../../context/AuthContext";

export default function Sidebar() {
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const handleLogout = async () => {
    try {
      await api.post("/auth/logout");

      setUser(null);
      navigate("/login");
    } catch (err) {
      console.error("Logout failed");
    }
  };

  return (
    <div className="w-64 h-screen bg-gray-800 text-white p-4 flex flex-col justify-between">
      <div>
        <h2 className="text-xl font-bold mb-6">SentinelGuard</h2>

        <nav className="flex flex-col gap-4">
          <Link to="/home" className="hover:text-gray-300">Home</Link>
          <Link to="/upload" className="hover:text-gray-300">Upload</Link>
          <Link to="/profile" className="hover:text-gray-300">Profile</Link>
        </nav>
      </div>

      {/* Logout Button */}
      <button
        onClick={handleLogout}
        className="mt-6 bg-red-500 hover:bg-red-600 text-white py-2 rounded"
      >
        Logout
      </button>
    </div>
  );
}
