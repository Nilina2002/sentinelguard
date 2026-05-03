import { useId, useState } from "react";
import api from "../api/client";
import { toast } from "react-toastify";
import Loading from "../components/Loading";
import { generateCanonicalEmbedding } from "../utils/embedding";

export default function Upload() {
  const inputId = useId();
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
      toast.error("Choose an image first");
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

      toast.success("Image uploaded to the feed");
      setFile(null);
      setPreview(null);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string } }; message?: string };
      toast.error(ax.response?.data?.message || ax.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading message="Uploading and indexing…" />;

  return (
    <div className="mx-auto max-w-xl space-y-8">
      <header>
        <p className="text-xs font-semibold uppercase tracking-widest text-teal-600">Share</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Upload an image</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          Images are fingerprinted for similarity search to support NCII reporting workflows. Use only content you are allowed to share.
        </p>
      </header>

      <div className="rounded-2xl border border-slate-200/80 bg-surface-elevated p-6 shadow-sm sm:p-8">
        <label
          htmlFor={inputId}
          className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50/80 px-6 py-12 transition hover:border-teal-400/60 hover:bg-teal-50/30"
        >
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-white text-teal-600 shadow-sm ring-1 ring-slate-200">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-slate-800">Drop a file here or click to browse</span>
          <span className="mt-1 text-xs text-slate-500">PNG, JPG, WebP — one image at a time</span>
          <input id={inputId} type="file" accept="image/*" onChange={handleFileChange} className="sr-only" />
        </label>

        {preview && (
          <div className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
            <img src={preview} alt="Preview" className="max-h-80 w-full object-contain" />
          </div>
        )}

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleUpload}
            disabled={!file || loading}
            className="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-teal-900/20 transition hover:from-teal-500 hover:to-cyan-500 disabled:pointer-events-none disabled:opacity-40"
          >
            Upload to feed
          </button>
          {file && (
            <span className="text-xs text-slate-500">
              Selected: <span className="font-medium text-slate-700">{file.name}</span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
