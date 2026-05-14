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
      toast.error("Please choose an image to upload.");
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

      toast.success("Your image is now live on the feed.");
      setFile(null);
      setPreview(null);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string } }; message?: string };
      toast.error(ax.response?.data?.message || ax.message || "Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading message="Uploading and indexing…" />;

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-16 top-6 h-32 w-32 rounded-full bg-sky-100/80 blur-3xl" />
          <div className="absolute bottom-0 left-1/3 h-28 w-28 rounded-full bg-emerald-100/60 blur-3xl" />
        </div>
        <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-slate-600">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              UPLOAD AN IMAGE
            </div>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              Images are fingerprinted for similarity search to support NCII reporting workflows. Share only content you have the right to post.
            </p>
          </div>
          <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 px-4 py-3 text-xs text-emerald-900 sm:max-w-xs">
            Files are processed securely and used only for verification and matching.
          </div>
        </div>
      </header>

      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <label
          htmlFor={inputId}
          className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-12 transition hover:border-brand/60 hover:bg-brand/5"
        >
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-white text-brand shadow-sm ring-1 ring-slate-200">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-slate-900">Drop a file here or click to browse</span>
          <span className="mt-1 text-xs text-slate-500">PNG, JPG, WebP — one image at a time</span>
          <input id={inputId} type="file" accept="image/*" onChange={handleFileChange} className="sr-only" />
        </label>

        {preview && (
          <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
            <img src={preview} alt="Preview" className="max-h-96 w-full object-contain" />
          </div>
        )}

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button type="button" onClick={handleUpload} disabled={!file || loading} className="btn-primary disabled:pointer-events-none disabled:opacity-40 cursor-pointer">
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
