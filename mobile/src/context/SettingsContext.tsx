import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { Platform } from 'react-native';
import { normalizeOpenAiKey } from '../openaiKey';

export { isLikelyOpenAiKey, maskOpenAiKey, normalizeOpenAiKey } from '../openaiKey';

type SettingsContextValue = {
  apiKey: string;
  apiBaseUrl: string;
  apiToken: string;
  setApiKey: (value: string) => Promise<void>;
  setApiBaseUrl: (value: string) => Promise<void>;
  setApiToken: (value: string) => Promise<void>;
  ready: boolean;
  hasOpenAiKey: boolean;
};

const SettingsContext = createContext<SettingsContextValue | null>(null);
const KEY = 'agroparts.openai_api_key';
const API_URL_KEY = 'agroparts.api_base_url';
const API_TOKEN_KEY = 'agroparts.api_token';

async function storageGet(key: string): Promise<string | null> {
  try {
    const value = await AsyncStorage.getItem(key);
    if (value != null) return value;
  } catch {
    // fallback below
  }
  if (Platform.OS === 'web' && typeof localStorage !== 'undefined') {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  }
  return null;
}

async function storageSet(key: string, value: string): Promise<void> {
  let asyncOk = false;
  try {
    await AsyncStorage.setItem(key, value);
    asyncOk = true;
  } catch {
    asyncOk = false;
  }
  if (Platform.OS === 'web' && typeof localStorage !== 'undefined') {
    try {
      localStorage.setItem(key, value);
      return;
    } catch {
      if (!asyncOk) throw new Error('Не удалось сохранить на устройстве (хранилище недоступно)');
    }
  }
  if (!asyncOk) {
    throw new Error('Не удалось сохранить на устройстве');
  }
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKeyState] = useState('');
  const [apiBaseUrl, setApiBaseUrlState] = useState('');
  const [apiToken, setApiTokenState] = useState('');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    Promise.all([storageGet(KEY), storageGet(API_URL_KEY), storageGet(API_TOKEN_KEY)])
      .then(([key, url, token]) => {
        if (key) setApiKeyState(normalizeOpenAiKey(key));
        if (url) setApiBaseUrlState(url.trim().replace(/\/+$/, ''));
        if (token) setApiTokenState(token.trim());
      })
      .finally(() => setReady(true));
  }, []);

  const value = useMemo<SettingsContextValue>(
    () => ({
      apiKey,
      apiBaseUrl,
      apiToken,
      ready,
      hasOpenAiKey: Boolean(normalizeOpenAiKey(apiKey)),
      setApiKey: async (next) => {
        const cleaned = normalizeOpenAiKey(next);
        await storageSet(KEY, cleaned);
        setApiKeyState(cleaned);
      },
      setApiBaseUrl: async (next) => {
        const cleaned = next.trim().replace(/\/+$/, '');
        await storageSet(API_URL_KEY, cleaned);
        setApiBaseUrlState(cleaned);
      },
      setApiToken: async (next) => {
        const cleaned = next.trim();
        await storageSet(API_TOKEN_KEY, cleaned);
        setApiTokenState(cleaned);
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
