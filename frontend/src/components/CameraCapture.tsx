import React, { useRef } from "react";
import Webcam from "react-webcam";

type CameraCaptureProps = {
  onCapture: (imageSrc: string) => void;
  onCancel: () => void;
};

const CameraCapture: React.FC<CameraCaptureProps> = ({
  onCapture,
  onCancel,
}) => {
  const webcamRef = useRef<Webcam | null>(null);

  const capture = () => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      onCapture(imageSrc);
    }
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <Webcam
        ref={webcamRef}
        screenshotFormat="image/png"
        className="rounded-lg w-64 h-64 object-cover"
        videoConstraints={{ facingMode: "user" }}
      />

      <div className="flex gap-3">
        <button
          onClick={capture}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          Capture
        </button>

        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-500 text-white rounded"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

export default CameraCapture;