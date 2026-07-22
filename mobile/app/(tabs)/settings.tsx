import { useEffect, useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { refreshCatalogFromApi } from '../../src/api';
import { useParts } from '../../src/catalog';
import {
  isLikelyOpenAiKey,
  maskOpenAiKey,
  normalizeOpenAiKey,
  useSettings,
} from '../../src/context/SettingsContext';
import { colors, spacing } from '../../src/theme';
import { APP_BUILD_LABEL, VISION_MODEL, VISION_PROVIDER } from '../../src/version';

export default function SettingsScreen() {
  const parts = useParts();
  const {
    apiKey,
    apiBaseUrl,
    apiToken,
    setApiKey,
    setApiBaseUrl,
    setApiToken,
    ready,
    hasOpenAiKey,
  } = useSettings();
  const [draftKey, setDraftKey] = useState('');
  const [draftUrl, setDraftUrl] = useState('');
  const [draftToken, setDraftToken] = useState('');
  const [showKey, setShowKey] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [status, setStatus] = useState('');

  useEffect(() => {
    if (!ready) return;
    setDraftKey(apiKey);
    setDraftUrl(apiBaseUrl);
    setDraftToken(apiToken);
  }, [apiKey, apiBaseUrl, apiToken, ready]);

  async function saveOpenAiKey() {
    const cleaned = normalizeOpenAiKey(draftKey);
    if (!cleaned) {
      Alert.alert('OpenAI ключ', 'Вставьте ключ вида sk-...');
      return;
    }
    if (!isLikelyOpenAiKey(cleaned)) {
      Alert.alert(
        'Проверьте ключ',
        'Обычно ключ OpenAI начинается с sk- и длиннее 20 символов. Сохранить всё равно?',
        [
          { text: 'Отмена', style: 'cancel' },
          {
            text: 'Сохранить',
            onPress: () => {
              void persistKey(cleaned);
            },
          },
        ],
      );
      return;
    }
    await persistKey(cleaned);
  }

  async function persistKey(cleaned: string) {
    setSaving(true);
    setStatus('');
    try {
      await setApiKey(cleaned);
      setDraftKey(cleaned);
      setStatus(`Ключ сохранён: ${maskOpenAiKey(cleaned)}`);
      Alert.alert('Готово', `OpenAI ключ сохранён на этом устройстве\n${maskOpenAiKey(cleaned)}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Не удалось сохранить ключ';
      setStatus(message);
      Alert.alert('Ошибка', message);
    } finally {
      setSaving(false);
    }
  }

  async function saveAll() {
    setSaving(true);
    setStatus('');
    try {
      const cleaned = normalizeOpenAiKey(draftKey);
      await setApiBaseUrl(draftUrl);
      await setApiToken(draftToken);
      if (cleaned) {
        await setApiKey(cleaned);
        setDraftKey(cleaned);
      }
      const keyNote = cleaned
        ? `\nOpenAI: ${maskOpenAiKey(cleaned)}`
        : hasOpenAiKey
          ? `\nOpenAI: ${maskOpenAiKey(apiKey)}`
          : '\nOpenAI ключ не задан';
      setStatus('Настройки сохранены');
      Alert.alert('Сохранено', `Настройки записаны на устройство.${keyNote}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Не удалось сохранить';
      setStatus(message);
      Alert.alert('Ошибка', message);
    } finally {
      setSaving(false);
    }
  }

  async function clearOpenAiKey() {
    setSaving(true);
    try {
      await setApiKey('');
      setDraftKey('');
      setStatus('OpenAI ключ удалён');
    } catch (error) {
      Alert.alert('Ошибка', error instanceof Error ? error.message : 'Не удалось удалить');
    } finally {
      setSaving(false);
    }
  }

  async function syncCatalog() {
    const url = draftUrl.trim() || apiBaseUrl;
    if (!url) {
      Alert.alert('Каталог', 'Сначала укажите URL API');
      return;
    }
    await setApiBaseUrl(url);
    await setApiToken(draftToken);
    setSyncing(true);
    try {
      const result = await refreshCatalogFromApi(url, draftToken || apiToken);
      if (!result.ok) {
        Alert.alert('Ошибка', result.message || 'Не удалось обновить каталог');
        return;
      }
      Alert.alert('Каталог обновлён', `Позиций: ${result.count ?? parts.length}`);
    } catch (error) {
      Alert.alert('Ошибка', error instanceof Error ? error.message : 'Сеть недоступна');
    } finally {
      setSyncing(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}
    >
      <ScrollView
        style={styles.flex}
        contentContainerStyle={styles.screen}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="on-drag"
      >
        <Text style={styles.title}>Настройки</Text>
        <Text style={styles.version}>
          {APP_BUILD_LABEL} · {VISION_PROVIDER} ({VISION_MODEL})
        </Text>
        <Text style={styles.text}>
          Локальный каталог: {parts.length} поз.
          {hasOpenAiKey
            ? `\nOpenAI: установлен (${maskOpenAiKey(apiKey)})`
            : '\nOpenAI: не установлен — фото бирок не работает'}
          {'\n'}Провайдер распознавания: только OpenAI (Gemini не используется).
        </Text>

        <View style={styles.box}>
          <Text style={styles.boxTitle}>OpenAI API Key</Text>
          <Text style={styles.text}>
            Нужен для вкладки «Фото». Скопируйте ключ с platform.openai.com и вставьте ниже.
            Начинается с sk-. Gemini / Google AI не поддерживаются.
          </Text>
          <TextInput
            value={draftKey}
            onChangeText={setDraftKey}
            placeholder="sk-proj-... или sk-..."
            placeholderTextColor={colors.inkMuted}
            autoCapitalize="none"
            autoCorrect={false}
            autoComplete="off"
            textContentType="none"
            importantForAutofill="no"
            spellCheck={false}
            secureTextEntry={!showKey}
            style={styles.input}
          />
          <View style={styles.row}>
            <Pressable style={styles.chip} onPress={() => setShowKey((v) => !v)}>
              <Text style={styles.chipText}>{showKey ? 'Скрыть' : 'Показать'}</Text>
            </Pressable>
            {hasOpenAiKey || draftKey ? (
              <Pressable style={styles.chip} onPress={() => void clearOpenAiKey()}>
                <Text style={[styles.chipText, styles.danger]}>Удалить</Text>
              </Pressable>
            ) : null}
          </View>
          <Pressable
            style={[styles.primary, saving && styles.disabled]}
            onPress={() => void saveOpenAiKey()}
            disabled={saving}
          >
            <Text style={styles.primaryText}>
              {saving ? 'Сохранение…' : 'Сохранить OpenAI ключ'}
            </Text>
          </Pressable>
          {status ? <Text style={styles.status}>{status}</Text> : null}
        </View>

        <Text style={styles.label}>URL API (AgroParts → 1С)</Text>
        <TextInput
          value={draftUrl}
          onChangeText={setDraftUrl}
          placeholder="http://192.168.1.10:8080"
          placeholderTextColor={colors.inkMuted}
          autoCapitalize="none"
          autoCorrect={false}
          autoComplete="off"
          keyboardType="url"
          style={styles.input}
        />

        <Text style={styles.label}>API Token сервера</Text>
        <TextInput
          value={draftToken}
          onChangeText={setDraftToken}
          placeholder="необязательно (это не OpenAI ключ)"
          placeholderTextColor={colors.inkMuted}
          autoCapitalize="none"
          autoCorrect={false}
          autoComplete="off"
          style={styles.input}
        />

        <Pressable
          style={[styles.secondary, saving && styles.disabled]}
          onPress={() => void saveAll()}
          disabled={saving}
        >
          <Text style={styles.secondaryText}>Сохранить все настройки</Text>
        </Pressable>
        <Pressable style={styles.secondary} onPress={() => void syncCatalog()} disabled={syncing}>
          <Text style={styles.secondaryText}>
            {syncing ? 'Обновление…' : 'Обновить каталог с сервера'}
          </Text>
        </Pressable>

        <View style={styles.box}>
          <Text style={styles.boxTitle}>Если ключ «не ставится»</Text>
          <Text style={styles.text}>
            1. Вставьте ключ в поле OpenAI (не в API Token){'\n'}
            2. Нажмите «Сохранить OpenAI ключ»{'\n'}
            3. Откройте вкладку Фото — предупреждение должно исчезнуть{'\n'}
            4. Ключ хранится только на этом телефоне
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  screen: {
    padding: spacing.md,
    gap: 12,
    paddingBottom: 40,
  },
  title: {
    fontFamily: 'DMSans_700Bold',
    fontSize: 22,
    color: colors.ink,
  },
  version: {
    fontFamily: 'DMSans_600SemiBold',
    fontSize: 13,
    color: colors.brand,
  },
  text: {
    fontFamily: 'DMSans_400Regular',
    fontSize: 14,
    color: colors.inkMuted,
    lineHeight: 20,
  },
  label: {
    marginTop: 8,
    fontFamily: 'DMSans_600SemiBold',
    color: colors.ink,
  },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontFamily: 'DMSans_400Regular',
    fontSize: 15,
    color: colors.ink,
  },
  primary: {
    backgroundColor: colors.brand,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  primaryText: {
    color: colors.white,
    fontFamily: 'DMSans_700Bold',
    fontSize: 16,
  },
  secondary: {
    backgroundColor: colors.surface,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.line,
    paddingVertical: 14,
    alignItems: 'center',
  },
  secondaryText: {
    color: colors.ink,
    fontFamily: 'DMSans_700Bold',
    fontSize: 15,
  },
  disabled: { opacity: 0.6 },
  box: {
    marginTop: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.line,
    gap: 10,
  },
  boxTitle: {
    fontFamily: 'DMSans_700Bold',
    color: colors.ink,
    fontSize: 16,
  },
  row: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  chip: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: colors.bg,
  },
  chipText: {
    fontFamily: 'DMSans_600SemiBold',
    color: colors.ink,
    fontSize: 13,
  },
  danger: { color: colors.danger },
  status: {
    fontFamily: 'DMSans_500Medium',
    color: colors.brand,
    fontSize: 13,
  },
});
