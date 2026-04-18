import React, { useState } from "react";
import CameraCapture from "./CameraCapture";
import Loading from "./Loading";
import { toast } from "react-toastify";
import axios from "axios";
import { base64ToFile } from "../utils/image";

type ReportModalProps = {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string;
};

const ReportModal: React.FC<ReportModalProps> = ({
  isOpen,
  onClose,
  imageUrl,
}) => {
  const [isCameraOn, setIsCameraOn] = useState<boolean>(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleCapture = (img: string) => {
    setCapturedImage(img);
    setIsCameraOn(false);
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);

      const selfieFile = base64ToFile(capturedImage!, "selfie.png");

      // fetch original image and convert to blob
      const res = await fetch(imageUrl);
      const blob = await res.blob();
      const reportedFile = new File([blob], "reported.png");

      const formData = new FormData();
      formData.append("selfie", selfieFile);
      formData.append("reported_image", reportedFile);

      const response = await axios.post(
        "http://localhost:8000/reports/verify",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      if (!response.data.success) {
        toast.error("Face verification failed ❌. Try again with a clearer selfie.");
        return
      } 
      setLoading(false);
      toast.success("Report submitted & verified ✅");
      onClose();

      
    } catch (err: any) {
      toast.error("An error occurred while submitting the report.");
    } finally {
      setLoading(false);
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

        {/* Start Camera */}
        {!isCameraOn && !capturedImage && (
          <button
            onClick={() => setIsCameraOn(true)}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
          >
            Start Camera
          </button>
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