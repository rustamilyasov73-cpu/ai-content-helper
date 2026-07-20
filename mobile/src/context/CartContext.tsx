import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { getPart } from '../catalog';
import type { CartItem, Order } from '../types';

type CartContextValue = {
  items: CartItem[];
  orders: Order[];
  ready: boolean;
  add: (partId: string, qty?: number) => void;
  setQty: (partId: string, qty: number) => void;
  remove: (partId: string) => void;
  clear: () => void;
  totalQty: number;
  totalPrice: number;
  placeOrder: (phone: string, comment: string) => Order | null;
};

const CartContext = createContext<CartContextValue | null>(null);
const CART_KEY = 'agroparts.cart';
const ORDERS_KEY = 'agroparts.orders';

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    Promise.all([AsyncStorage.getItem(CART_KEY), AsyncStorage.getItem(ORDERS_KEY)])
      .then(([cartRaw, ordersRaw]) => {
        if (cartRaw) setItems(JSON.parse(cartRaw) as CartItem[]);
        if (ordersRaw) setOrders(JSON.parse(ordersRaw) as Order[]);
      })
      .finally(() => setReady(true));
  }, []);

  useEffect(() => {
    if (!ready) return;
    void AsyncStorage.setItem(CART_KEY, JSON.stringify(items));
  }, [items, ready]);

  useEffect(() => {
    if (!ready) return;
    void AsyncStorage.setItem(ORDERS_KEY, JSON.stringify(orders));
  }, [orders, ready]);

  const value = useMemo<CartContextValue>(() => {
    const totalQty = items.reduce((sum, item) => sum + item.qty, 0);
    const totalPrice = items.reduce((sum, item) => {
      const part = getPart(item.partId);
      return sum + (part ? part.price * item.qty : 0);
    }, 0);

    return {
      items,
      orders,
      ready,
      totalQty,
      totalPrice,
      add: (partId, qty = 1) => {
        const part = getPart(partId);
        if (!part || part.stock <= 0) return;
        setItems((prev) => {
          const existing = prev.find((i) => i.partId === partId);
          if (!existing) {
            return [...prev, { partId, qty: Math.min(qty, part.stock) }];
          }
          return prev.map((i) =>
            i.partId === partId ? { ...i, qty: Math.min(i.qty + qty, part.stock) } : i,
          );
        });
      },
      setQty: (partId, qty) => {
        const part = getPart(partId);
        if (!part) return;
        if (qty <= 0) {
          setItems((prev) => prev.filter((i) => i.partId !== partId));
          return;
        }
        setItems((prev) =>
          prev.map((i) => (i.partId === partId ? { ...i, qty: Math.min(qty, part.stock) } : i)),
        );
      },
      remove: (partId) => setItems((prev) => prev.filter((i) => i.partId !== partId)),
      clear: () => setItems([]),
      placeOrder: (phone, comment) => {
        if (!items.length || !phone.trim()) return null;
        const orderItems = items
          .map((item) => {
            const part = getPart(item.partId);
            if (!part) return null;
            return {
              partId: part.id,
              sku: part.sku,
              name: part.name,
              qty: item.qty,
              price: part.price,
            };
          })
          .filter(Boolean) as Order['items'];
        if (!orderItems.length) return null;
        const order: Order = {
          id: `ord-${Date.now()}`,
          createdAt: new Date().toISOString(),
          phone: phone.trim(),
          comment: comment.trim(),
          items: orderItems,
          total: orderItems.reduce((s, i) => s + i.price * i.qty, 0),
        };
        setOrders((prev) => [order, ...prev]);
        setItems([]);
        return order;
      },
    };
  }, [items, orders, ready]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart outside provider');
  return ctx;
}
