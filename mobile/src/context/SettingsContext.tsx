import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

type SettingsContextValue = {
  apiKey: string;
  apiBaseUrl: string;
  apiToken: string;
  setApiKey: (value: string) => Promise<void>;
  setApiBaseUrl: (value: string) => Promise<void>;
  setApiToken: (value: string) => Promise<void>;
  ready: boolean;
};

const SettingsContext = createContext<SettingsContextValue | null>(null);
const KEY = 'agroparts.openai_api_key';
const API_URL_KEY = 'agroparts.api_base_url';
const API_TOKEN_KEY = 'agroparts.api_token';

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKeyState] = useState('');
  const [apiBaseUrl, setApiBaseUrlState] = useState('');
  const [apiToken, setApiTokenState] = useState('');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    Promise.all([
      AsyncStorage.getItem(KEY),
      AsyncStorage.getItem(API_URL_KEY),
      AsyncStorage.getItem(API_TOKEN_KEY),
    ])
      .then(([key, url, token]) => {
        if (key) setApiKeyState(key);
        if (url) setApiBaseUrlState(url);
        if (token) setApiTokenState(token);
      })
      .finally(() => setReady(true));
  }, []);

  const value = useMemo<SettingsContextValue>(
    () => ({
      apiKey,
      apiBaseUrl,
      apiToken,
      ready,
      setApiKey: async (next) => {
        setApiKeyState(next);
        await AsyncStorage.setItem(KEY, next.trim());
      },
      setApiBaseUrl: async (next) => {
        const value = next.trim().replace(/\/+$/, '');
        setApiBaseUrlState(value);
        await AsyncStorage.setItem(API_URL_KEY, value);
      },
      setApiToken: async (next) => {
        setApiTokenState(next.trim());
        await AsyncStorage.setItem(API_TOKEN_KEY, next.trim());
      },
    }),
    [apiKey, apiBaseUrl, apiToken, ready],
  );

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings outside provider');
  return ctx;
}
