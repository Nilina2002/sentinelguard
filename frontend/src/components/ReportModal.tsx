import React, { useEffect, useState } from "react";
import CameraCapture from "./CameraCapture";
import Loading from "./Loading";
import { toast } from "react-toastify";
import { base64ToFile } from "../utils/image";
import api from "../api/client";

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
  const [supportingImageFile, setSupportingImageFile] = useState<File | null>(null);
  const [supportingImagePreview, setSupportingImagePreview] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [reportId, setReportId] = useState<number | null>(null);
  const [faceEligible, setFaceEligible] = useState<boolean>(false);
  const [checkingFace, setCheckingFace] = useState<boolean>(false);
  const [stepStatus, setStepStatus] = useState({
    faceCheck: "pending",
    selfieVerify: "pending",
    supportVerify: "pending",
    finalize: "pending",
  });

  if (!isOpen) return null;

  useEffect(() => {
    if (!isOpen) {
      setReportId(null);
      setFaceEligible(false);
      setCheckingFace(false);
      setCapturedImage(null);
      setIsCameraOn(false);
      setSupportingImageFile(null);
      setSupportingImagePreview(null);
      setStepStatus({
        faceCheck: "pending",
        selfieVerify: "pending",
        supportVerify: "pending",
        finalize: "pending",
      });
    }
  }, [isOpen]);

  const handleCapture = (img: string) => {
    setCapturedImage(img);
    setIsCameraOn(false);
  };

  const handleSupportingImageChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const selected = event.target.files?.[0];
    if (!selected) return;

    if (supportingImagePreview) {
      URL.revokeObjectURL(supportingImagePreview);
    }

    setSupportingImageFile(selected);
    setSupportingImagePreview(URL.createObjectURL(selected));
  };

  const reasonMessage = (reasonCode?: string) => {
    const reasons: Record<string, string> = {
      NO_FACE_DETECTED: "No face detected in the reported image.",
      SELFIE_FACE_COUNT_INVALID: "Your selfie must contain exactly one face.",
      LIVENESS_CHECK_FAILED:
        "Selfie liveness check failed. Try again in better lighting.",
      SELFIE_MISMATCH: "Selfie does not match the reported image face.",
      SUPPORTING_EVIDENCE_MISMATCH:
        "Supporting image does not match required thresholds.",
      FINAL_THRESHOLD_FAILED: "Final confidence is below approval threshold.",
    };
    return reasons[reasonCode || ""] || "Verification failed. Please try again.";
  };

  const submitReport = async () => {
    try {
      setLoading(true);
      setStepStatus({
        faceCheck: "pending",
        selfieVerify: "pending",
        supportVerify: "pending",
        finalize: "pending",
      });

      if (!capturedImage) {
        toast.error("Please capture a selfie first.");
        return;
      }

      if (!supportingImageFile) {
        toast.error("Please upload a supporting image.");
        return;
      }

      if (!reportId || !faceEligible) {
        toast.error("Reported image must pass face check before selfie verification.");
        return;
      }

      setStepStatus((prev) => ({ ...prev, selfieVerify: "in_progress" }));
      const selfieFile = base64ToFile(capturedImage, "selfie.png");
      const selfieForm = new FormData();
      selfieForm.append("selfie", selfieFile);
      const selfieRes = await api.post(`/reports/${reportId}/selfie-verify`, selfieForm, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      if (!selfieRes.data.success) {
        setStepStatus((prev) => ({ ...prev, selfieVerify: "failed" }));
        toast.error(reasonMessage(selfieRes.data?.data?.reason_code));
        return;
      }
      setStepStatus((prev) => ({ ...prev, selfieVerify: "passed" }));

      setStepStatus((prev) => ({ ...prev, supportVerify: "in_progress" }));
      const supportForm = new FormData();
      supportForm.append("supporting_image", supportingImageFile);
      const supportRes = await api.post(
        `/reports/${reportId}/supporting-evidence-verify`,
        supportForm,
        {
          headers: { "Content-Type": "multipart/form-data" },
        },
      );
      if (!supportRes.data.success) {
        setStepStatus((prev) => ({ ...prev, supportVerify: "failed" }));
        toast.error(reasonMessage(supportRes.data?.data?.reason_code));
        return;
      }
      setStepStatus((prev) => ({ ...prev, supportVerify: "passed" }));

      setStepStatus((prev) => ({ ...prev, finalize: "in_progress" }));
      const finalizeRes = await api.post(`/reports/${reportId}/finalize`);
      if (!finalizeRes.data.success) {
        setStepStatus((prev) => ({ ...prev, finalize: "failed" }));
        toast.error(reasonMessage(finalizeRes.data?.data?.reason_code));
        return;
      }
      setStepStatus((prev) => ({ ...prev, finalize: "passed" }));

      toast.success("Ownership verified and reported image removed.");
      onClose();
    } catch (err: any) {
      const reasonCode = err?.response?.data?.data?.reason_code;
      toast.error(reasonMessage(reasonCode));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    await submitReport();
  };

  const handleCheckReportedFace = async () => {
    try {
      setCheckingFace(true);
      setStepStatus((prev) => ({ ...prev, faceCheck: "in_progress" }));
      const reportRes = await api.post("/reports/", { target_image_id: imageId });
      const createdReportId = reportRes.data.id;
      const faceCheck = await api.post(`/reports/${createdReportId}/face-presence-check`);
      if (!faceCheck.data.success) {
        setStepStatus((prev) => ({ ...prev, faceCheck: "failed" }));
        setFaceEligible(false);
        toast.error(reasonMessage(faceCheck.data?.data?.reason_code));
        return;
      }
      setReportId(createdReportId);
      setFaceEligible(true);
      setStepStatus((prev) => ({ ...prev, faceCheck: "passed" }));
      toast.success("Face detected in reported image. Selfie upload is now enabled.");
    } catch (err: any) {
      const reasonCode = err?.response?.data?.data?.reason_code;
      setFaceEligible(false);
      setStepStatus((prev) => ({ ...prev, faceCheck: "failed" }));
      toast.error(reasonMessage(reasonCode));
    } finally {
      setCheckingFace(false);
    }
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

        {/* Supporting Image Upload */}
        <div className="mt-4 text-left">
          <label className="text-sm text-gray-700 font-medium block mb-2">
            Upload supporting image (required)
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={handleSupportingImageChange}
            className="w-full text-sm"
          />
          {supportingImagePreview && (
            <img
              src={supportingImagePreview}
              alt="Supporting preview"
              className="mt-3 w-full h-40 object-cover rounded"
            />
          )}
        </div>

        {!faceEligible && (
          <div className="mt-4">
            <button
              onClick={handleCheckReportedFace}
              disabled={checkingFace}
              className="px-4 py-2 bg-indigo-600 text-white rounded"
            >
              {checkingFace ? "Checking face..." : "Check Face in Reported Image"}
            </button>
            <p className="text-xs text-gray-500 mt-2">
              Selfie capture is enabled only when the reported image contains a face.
            </p>
          </div>
        )}

        {/* Start Camera */}
        {faceEligible && !isCameraOn && !capturedImage && (
          <div className="mt-4 flex justify-center gap-3">
            <button
              onClick={() => setIsCameraOn(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded"
            >
              Start Camera
            </button>
          </div>
        )}

        {/* Camera */}
        {faceEligible && isCameraOn && (
          <div className="mt-4">
            <CameraCapture
              onCapture={handleCapture}
              onCancel={() => setIsCameraOn(false)}
            />
          </div>
        )}

        {/* Preview */}
        {faceEligible && capturedImage && (
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

        <div className="mt-4 text-left text-xs text-gray-700 space-y-1">
          <p>1. Face check: {stepStatus.faceCheck}</p>
          <p>2. Selfie verification: {stepStatus.selfieVerify}</p>
          <p>3. Supporting verification: {stepStatus.supportVerify}</p>
          <p>4. Finalize removal: {stepStatus.finalize}</p>
        </div>

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