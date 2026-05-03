const TARGET_SIZE = 64;
const EMBEDDING_DIM = 512;

type FloatVector = number[];

const l2Normalize = (vector: FloatVector): FloatVector => {
  const norm = Math.sqrt(vector.reduce((sum, v) => sum + v * v, 0));
  if (!norm) return vector.map(() => 0);
  return vector.map((v) => v / norm);
};

const averageVectors = (vectors: FloatVector[]): FloatVector => {
  if (!vectors.length) return [];
  const out = new Array(vectors[0].length).fill(0);
  for (const vec of vectors) {
    for (let i = 0; i < vec.length; i += 1) {
      out[i] += vec[i];
    }
  }
  return out.map((value) => value / vectors.length);
};

const drawTransformed = (
  image: CanvasImageSource,
  mode: "original" | "flip" | "centerCrop" | "brightened",
): HTMLCanvasElement => {
  const canvas = document.createElement("canvas");
  canvas.width = TARGET_SIZE;
  canvas.height = TARGET_SIZE;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Unable to create canvas context");
  }

  if (mode === "flip") {
    ctx.translate(TARGET_SIZE, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(image, 0, 0, TARGET_SIZE, TARGET_SIZE);
    return canvas;
  }

  if (mode === "centerCrop") {
    const sourceWidth = (image as HTMLImageElement).naturalWidth || (image as any).videoWidth || TARGET_SIZE;
    const sourceHeight = (image as HTMLImageElement).naturalHeight || (image as any).videoHeight || TARGET_SIZE;
    const side = Math.min(sourceWidth, sourceHeight);
    const sx = Math.max(0, (sourceWidth - side) / 2);
    const sy = Math.max(0, (sourceHeight - side) / 2);
    ctx.drawImage(image, sx, sy, side, side, 0, 0, TARGET_SIZE, TARGET_SIZE);
    return canvas;
  }

  ctx.drawImage(image, 0, 0, TARGET_SIZE, TARGET_SIZE);

  if (mode === "brightened") {
    const imageData = ctx.getImageData(0, 0, TARGET_SIZE, TARGET_SIZE);
    const pixels = imageData.data;
    for (let i = 0; i < pixels.length; i += 4) {
      pixels[i] = Math.min(255, pixels[i] * 1.05 + 4);
      pixels[i + 1] = Math.min(255, pixels[i + 1] * 1.05 + 4);
      pixels[i + 2] = Math.min(255, pixels[i + 2] * 1.05 + 4);
    }
    ctx.putImageData(imageData, 0, 0);
  }

  return canvas;
};

const computeDescriptor = (canvas: HTMLCanvasElement): FloatVector => {
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("Unable to compute descriptor");

  const { data } = ctx.getImageData(0, 0, TARGET_SIZE, TARGET_SIZE);
  const gray = new Float32Array(TARGET_SIZE * TARGET_SIZE);

  for (let i = 0; i < gray.length; i += 1) {
    const px = i * 4;
    gray[i] = 0.299 * data[px] + 0.587 * data[px + 1] + 0.114 * data[px + 2];
  }

  const pooledGray: number[] = [];
  const pooledGrad: number[] = [];

  for (let y = 0; y < TARGET_SIZE; y += 4) {
    for (let x = 0; x < TARGET_SIZE; x += 4) {
      let sumGray = 0;
      let sumGrad = 0;
      let count = 0;
      for (let oy = 0; oy < 4; oy += 1) {
        for (let ox = 0; ox < 4; ox += 1) {
          const yy = y + oy;
          const xx = x + ox;
          const idx = yy * TARGET_SIZE + xx;
          const left = yy * TARGET_SIZE + Math.max(0, xx - 1);
          const right = yy * TARGET_SIZE + Math.min(TARGET_SIZE - 1, xx + 1);
          const up = Math.max(0, yy - 1) * TARGET_SIZE + xx;
          const down = Math.min(TARGET_SIZE - 1, yy + 1) * TARGET_SIZE + xx;

          const gx = gray[right] - gray[left];
          const gy = gray[down] - gray[up];
          const grad = Math.sqrt(gx * gx + gy * gy);

          sumGray += gray[idx] / 255;
          sumGrad += grad / 255;
          count += 1;
        }
      }
      pooledGray.push(sumGray / count);
      pooledGrad.push(sumGrad / count);
    }
  }

  const vector = [...pooledGray, ...pooledGrad];
  if (vector.length !== EMBEDDING_DIM) {
    throw new Error(`Embedding dimension mismatch: ${vector.length}`);
  }

  return l2Normalize(vector);
};

const loadImageElement = (file: File): Promise<HTMLImageElement> =>
  new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Failed to decode image"));
    image.src = URL.createObjectURL(file);
  });

export const generateCanonicalEmbedding = async (file: File): Promise<FloatVector> => {
  const image = await loadImageElement(file);

  try {
    const views: Array<"original" | "flip" | "centerCrop" | "brightened"> = [
      "original",
      "flip",
      "centerCrop",
      "brightened",
    ];

    const descriptors = views.map((mode) => computeDescriptor(drawTransformed(image, mode)));
    return l2Normalize(averageVectors(descriptors));
  } finally {
    URL.revokeObjectURL(image.src);
  }
};
