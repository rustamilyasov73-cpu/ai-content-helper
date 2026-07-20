import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

type SettingsContextValue = {
  apiKey: string;
  setApiKey: (value: string) => Promise<void>;
  ready: boolean;
};

const SettingsContext = createContext<SettingsContextValue | null>(null);
const KEY = 'agroparts.openai_api_key';

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKeyState] = useState('');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(KEY)
      .then((value) => {
        if (value) setApiKeyState(value);
      })
      .finally(() => setReady(true));
  }, []);

  const value = useMemo<SettingsContextValue>(
    () => ({
      apiKey,
      ready,
      setApiKey: async (next) => {
        setApiKeyState(next);
        await AsyncStorage.setItem(KEY, next.trim());
      },
    }),
    [apiKey, ready],
  );

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings outside provider');
  return ctx;
}
