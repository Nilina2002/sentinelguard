import React, { useState } from "react";
import CameraCapture from "./CameraCapture";
import { toast } from "react-toastify";
import { base64ToFile } from "../utils/image";
import api from "../api/client";
import { generateCanonicalEmbedding } from "../utils/embedding";
import Loading from "../components/Loading";

type ReportModalProps = {
  isOpen: boolean;
  onClose: () => void;
  imageId: number;
  imageUrl: string;
};

const ReportModal: React.FC<ReportModalProps> = ({ isOpen, onClose, imageId, imageUrl }) => {
  const [isCameraOn, setIsCameraOn] = useState<boolean>(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [claimImageFile, setClaimImageFile] = useState<File | null>(null);
  const [claimImagePreview, setClaimImagePreview] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>("Preparing your report...");

  if (!isOpen) return null;

  const handleCapture = (img: string) => {
    setCapturedImage(img);
    setIsCameraOn(false);
  };

  const handleClaimImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    if (!selected) return;

    if (claimImagePreview) {
      URL.revokeObjectURL(claimImagePreview);
    }

    setClaimImageFile(selected);
    setClaimImagePreview(URL.createObjectURL(selected));
  };

  const submitReport = async (skipVerification: boolean) => {
    try {
      setLoading(true);
      setLoadingMessage("Preparing report data...");

      const res = await fetch(imageUrl);
      const blob = await res.blob();
      const reportedFile = new File([blob], "reported.png");
      const queryFile = claimImageFile ?? reportedFile;

      if (!skipVerification) {
        if (!capturedImage) {
          toast.error("Please capture a selfie to verify your identity.");
          return;
        }

        setLoadingMessage("Verifying identity...");
        const selfieFile = base64ToFile(capturedImage, "selfie.png");
        const formData = new FormData();
        formData.append("selfie", selfieFile);
        formData.append("reported_image", reportedFile);

        const response = await api.post("/reports/verify", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        if (!response.data.success) {
          toast.error(response.data.message || "Verification failed. Try a clearer, well-lit selfie.");
          return;
        }
        toast.success("Identity verified successfully.");
      }

      if (!claimImageFile) {
        toast.error("Please upload the claim image before submitting.");
        return;
      }

      setLoadingMessage("Creating report record...");
      const reportRes = await api.post("/reports/");
      const reportId = reportRes.data.id;

      setLoadingMessage("Generating secure match embedding...");
      const embedding = await generateCanonicalEmbedding(queryFile);
      setLoadingMessage("Submitting for match analysis...");
      const embedRes = await api.post(`/reports/${reportId}/embedding`, {
        verified: !skipVerification,
        embedding,
        target_image_id: imageId,
      });

      if (!embedRes.data?.success) {
        toast.error(embedRes.data?.message || "Report submitted, but matching did not complete.");
        return;
      }

      const matchesFound = embedRes.data?.data?.matches_found ?? 0;
      toast.success("Report submitted and verified.");
      if (matchesFound > 0) {
        toast.info("Claim image matched. The reported image was removed.");
      } else {
        toast.info("No strong match was found. Your report has been recorded.");
      }
      onClose();
      window.location.reload();
    } catch (error: any) {
      toast.error(error.message || "Something went wrong while submitting the report.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    await submitReport(false);
  };

  if (loading) return <Loading message={loadingMessage || "Loading..."} />;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="report-modal-title"
    >
      <div className="relative max-h-[min(90vh,720px)] w-full max-w-lg overflow-y-auto rounded-3xl border border-slate-200 bg-white shadow-2xl shadow-slate-900/25">
        <div className="sticky top-0 z-[1] flex items-start justify-between gap-4 border-b border-slate-100 bg-white/95 px-5 py-4 backdrop-blur-sm sm:px-6">
          <div>
            <h2 id="report-modal-title" className="text-lg font-bold tracking-tight text-slate-900">
              Report content
            </h2>
            <p className="mt-1 text-xs leading-relaxed text-slate-500">
              NCII removal requests require a claim image. Identity verification uses a live selfie when enabled.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-5 px-5 py-5 sm:px-6 sm:py-6">
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
            <img src={imageUrl} alt="Reported content" className="max-h-52 w-full object-contain" />
          </div>

          <section className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-600">Claim image</h3>
            <p className="mt-1 text-xs text-slate-500">Required — the image you are asserting rights over or matching for removal.</p>
            <label className="mt-3 flex cursor-pointer items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white px-3 py-6 text-sm font-medium text-brand transition hover:border-brand/60 hover:bg-brand/5">
              <input type="file" accept="image/*" onChange={handleClaimImageChange} className="sr-only" />
              {claimImageFile ? "Replace file" : "Choose file"}
            </label>
            {claimImagePreview && (
              <img src={claimImagePreview} alt="Claim preview" className="mt-3 max-h-40 w-full rounded-lg border border-slate-200 object-contain" />
            )}
          </section>

          {!isCameraOn && !capturedImage && (
            <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
              <button
                type="button"
                onClick={() => setIsCameraOn(true)}
                className="btn-primary flex-1 gap-2 cursor-pointer"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Verify with your Live Selfie
              </button>
            </div>
          )}

          {isCameraOn && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <CameraCapture onCapture={handleCapture} onCancel={() => setIsCameraOn(false)} />
            </div>
          )}

          {capturedImage && (
            <div className="rounded-2xl border border-emerald-100 bg-emerald-50/60 p-4 text-center">
              <p className="text-xs font-medium uppercase tracking-wide text-emerald-800">Selfie captured</p>
              <img src={capturedImage} alt="Your selfie" className="mx-auto mt-3 h-28 w-28 rounded-full border-4 border-white object-cover shadow-md" />
              <div className="mt-4 flex justify-center gap-2">
                <button
                  type="button"
                  onClick={() => setCapturedImage(null)}
                  className="btn-ghost cursor-pointer"
                >
                  Retake
                </button>
                <button
                  type="button"
                  onClick={handleSubmit}
                  className="btn-primary cursor-pointer"
                >
                  Submit report
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportModal;
