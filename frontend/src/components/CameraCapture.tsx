import React, { useRef } from "react";
import Webcam from "react-webcam";

type CameraCaptureProps = {
  onCapture: (imageSrc: string) => void;
  onCancel: () => void;
};

const CameraCapture: React.FC<CameraCaptureProps> = ({ onCapture, onCancel }) => {
  const webcamRef = useRef<Webcam | null>(null);

  const capture = () => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      onCapture(imageSrc);
    }
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <Webcam
        ref={webcamRef}
        screenshotFormat="image/png"
        className="aspect-square w-full max-w-sm rounded-xl border border-slate-200 object-cover shadow-inner"
        videoConstraints={{ facingMode: "user" }}
      />

      <div className="flex w-full max-w-sm flex-wrap justify-center gap-2">
        <button
          type="button"
          onClick={capture}
          className="inline-flex flex-1 min-w-[120px] items-center justify-center rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:from-teal-500 hover:to-cyan-500"
        >
          Capture
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex flex-1 min-w-[120px] items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

export default CameraCapture;
