import { useEffect, useState } from "react";
import api from "../api/client";
import ImageCard from "../components/ImageCard";
import { toast } from "react-toastify";
import Loading from "../components/Loading";

interface ImageType {
  id: number;
  image_url: string;
}

export default function Home() {
  const [images, setImages] = useState<ImageType[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchImages = async () => {
    try {
      const res = await api.get("/images");
      setImages(res.data);
    } catch (err) {
      toast.error("Failed to fetch images");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, []);

  if (loading) return <Loading message="Loading feed..." />;
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Home Feed</h2>

      {images.length === 0 ? (
        <p>No images uploaded yet.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {images.map((img) => (
            <ImageCard key={img.id} {...img} />
          ))}
        </div>
      )}
    </div>
  );
}