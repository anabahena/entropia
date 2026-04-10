export type WindowRecord = {
  id: number;
  image_path: string;
  sha256: string;
  perceptual_hash: string;
  description: string | null;
  structured_data: unknown;
  created_at: string;
};
