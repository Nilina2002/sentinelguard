import React, { useState } from "react";
import CameraCapture from "./CameraCapture";
import Loading from "./Loading";
import { toast } from "react-toastify";
import { base64ToFile } from "../utils/image";
import api from "../api/client";
import { generateCanonicalEmbedding } from "../utils/embedding";

type ReportModalProps = {
  isOpen: boolean;
  onClose: () => void;
  imageId: number;
  imageUrl: string;
};

const ReportModal: React.FC<ReportModalProps> = ({
  isOpen,
  onClose,
  imageId,
  imageUrl,
}) => {
  const [isCameraOn, setIsCameraOn] = useState<boolean>(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [claimImageFile, setClaimImageFile] = useState<File | null>(null);
  const [claimImagePreview, setClaimImagePreview] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

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

      // fetch original image and convert to blob
      const res = await fetch(imageUrl);
      const blob = await res.blob();
      const reportedFile = new File([blob], "reported.png");
      const queryFile = claimImageFile ?? reportedFile;

      if (!skipVerification) {
        if (!capturedImage) {
          toast.error("Please capture a selfie first.");
          return;
        }

        const selfieFile = base64ToFile(capturedImage, "selfie.png");
        const formData = new FormData();
        formData.append("selfie", selfieFile);
        formData.append("reported_image", reportedFile);

        const response = await api.post("/reports/verify", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        if (!response.data.success) {
          toast.error("Face verification failed ❌. Try again with a clearer selfie.");
          return;
        }
      }

      if (!claimImageFile) {
        toast.error("Please upload the claim image before submitting.");
        return;
      }

      const reportRes = await api.post("/reports/");
      const reportId = reportRes.data.id;

      const embedding = await generateCanonicalEmbedding(queryFile);
      const embedRes = await api.post(`/reports/${reportId}/embedding`, {
        verified: true,
        embedding,
        target_image_id: imageId,
      });

      const matchesFound = embedRes.data?.data?.matches_found ?? 0;
      toast.success(
        skipVerification
          ? "Report submitted (verification skipped) ✅"
          : "Report submitted & verified ✅",
      );
      if (matchesFound > 0) {
        toast.info("Claim image matched. The reported image was removed.");
      }
      onClose();
    } catch (err: any) {
      toast.error("An error occurred while submitting the report.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    await submitReport(false);
  };

  const handleSkipVerification = async () => {
    await submitReport(true);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-xl w-[400px] text-center">
        <h2 className="text-lg font-semibold mb-3">Report Image</h2>

        {/* Original Image */}
        <img
          src={imageUrl}
          alt="Original"
          className="w-full h-48 object-cover rounded"
        />

        {/* Claim Image Upload */}
        <div className="mt-4 text-left">
          <label className="text-sm text-gray-700 font-medium block mb-2">
            Upload the claim image (required)
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={handleClaimImageChange}
            className="w-full text-sm"
          />
          {claimImagePreview && (
            <img
              src={claimImagePreview}
              alt="Claim preview"
              className="mt-3 w-full h-40 object-cover rounded"
            />
          )}
        </div>

        {/* Start Camera */}
        {!isCameraOn && !capturedImage && (
          <div className="mt-4 flex justify-center gap-3">
            <button
              onClick={() => setIsCameraOn(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded"
            >
              Start Camera
            </button>
            <button
              onClick={handleSkipVerification}
              className="px-4 py-2 bg-amber-600 text-white rounded"
            >
              Skip (Test)
            </button>
          </div>
        )}

        {/* Camera */}
        {isCameraOn && (
          <div className="mt-4">
            <CameraCapture
              onCapture={handleCapture}
              onCancel={() => setIsCameraOn(false)}
            />
          </div>
        )}

        {/* Preview */}
        {capturedImage && (
          <div className="mt-4 flex flex-col items-center">
            <p className="text-sm text-gray-600 mb-2">
              Confirm your selfie
            </p>

            <img
              src={capturedImage}
              alt="Captured"
              className="w-32 h-32 object-cover rounded-full"
            />

            <div className="flex gap-3 mt-4">
              <button
                onClick={() => setCapturedImage(null)}
                className="px-4 py-2 bg-gray-500 text-white rounded"
              >
                Retake
              </button>

              <button
                onClick={handleSubmit}
                className="px-4 py-2 bg-green-600 text-white rounded"
              >
                Submit
              </button>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && <Loading message="Submitting report..." />}

        {/* Close */}
        <button
          onClick={onClose}
          className="mt-4 text-sm text-red-500"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default ReportModal;