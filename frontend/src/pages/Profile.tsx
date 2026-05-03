import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { user } = useAuth();

  return (
    <div>
      <h2 className="text-xl font-bold">Profile</h2>
      <p>Email: {user?.data.email}</p>
    </div>
  );
}
