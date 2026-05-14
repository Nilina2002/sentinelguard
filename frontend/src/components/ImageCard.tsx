import { useState } from "react";
import ReportModal from "./ReportModal";

interface ImageProps {
  id: number;
  image_url: string;
}

export default function ImageCard({ id, image_url }: ImageProps) {
  const normalizedPath = image_url.replace(/\\/g, '/');
  const imageUrl = `http://localhost:8000/${normalizedPath}`;

  const [open, setOpen] = useState(false);
  
  return (
    <>
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <img
            src={imageUrl}
            alt={`Image ${id}`}
            className="w-full h-64 object-cover"
            onError={(e) => {
                (e.target as HTMLImageElement).src = '/placeholder-image.jpg';
                console.error(`Failed to load image: ${imageUrl}`);
            }}
            />

            <div className="p-3 flex justify-between items-center">
            <span className="text-sm text-gray-600">Image #{id}</span>
            <button className="text-red-500 text-sm hover:underline" onClick={() => setOpen(true)}>
                Report
            </button>
            </div>
        </div>

        {open && (
            <ReportModal
                isOpen={open}
                imageId={id}
                imageUrl={imageUrl}
                onClose={() => setOpen(false)}
            />
        )}
    </>

  );
}