import { useState } from "react";
import api from "../api/client";
import { toast } from "react-toastify";
import Loading from "../components/Loading";
import { generateCanonicalEmbedding } from "../utils/embedding";

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

    setFile(selected);
    setPreview(URL.createObjectURL(selected));
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error("Please select a file first");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      const embedding = await generateCanonicalEmbedding(file);
      formData.append("embedding", JSON.stringify(embedding));

      const res = await api.post("/images/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      if (!res.data.success) throw new Error(res.data.message || "Upload failed");

      toast.success("Upload successful");

      // reset
      setFile(null);
      setPreview(null);
    } catch (err: any) {
      toast.error(err.response?.data?.message || err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading message="Uploading image..." />;

  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Upload Image</h2>

      {/* File Input */}
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="mb-4"
      />

      {/* Preview */}
      {preview && (
        <div className="mb-4">
          <img
            src={preview}
            alt="preview"
            className="w-full h-64 object-cover rounded"
          />
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={loading}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        {loading ? "Uploading..." : "Upload"}
      </button>
    </div>
  );
}