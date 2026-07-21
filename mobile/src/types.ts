export type Part = {
  id: string;
  sku: string;
  name: string;
  category: string;
  brand: string;
  compatible: string[];
  price: number;
  stock: number;
  unit: string;
  description: string;
};

export type CartItem = {
  partId: string;
  qty: number;
};

export type Order = {
  id: string;
  createdAt: string;
  phone: string;
  comment: string;
  items: Array<{
    partId: string;
    sku: string;
    name: string;
    qty: number;
    price: number;
  }>;
  total: number;
};

export type PhotoRecognition = {
  rawText: string;
  candidates: string[];
  brand: string;
  model: string;
  notes: string;
  error?: string;
};
