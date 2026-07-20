import { useEffect, useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { refreshCatalogFromApi } from '../../src/api';
import { useParts } from '../../src/catalog';
import { useSettings } from '../../src/context/SettingsContext';
import { colors, spacing } from '../../src/theme';

export default function SettingsScreen() {
  const parts = useParts();
  const { apiKey, apiBaseUrl, apiToken, setApiKey, setApiBaseUrl, setApiToken, ready } =
    useSettings();
  const [draftKey, setDraftKey] = useState('');
  const [draftUrl, setDraftUrl] = useState('');
  const [draftToken, setDraftToken] = useState('');
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    if (!ready) return;
    setDraftKey(apiKey);
    setDraftUrl(apiBaseUrl);
    setDraftToken(apiToken);
  }, [apiKey, apiBaseUrl, apiToken, ready]);

  async function save() {
    await setApiKey(draftKey);
    await setApiBaseUrl(draftUrl);
    await setApiToken(draftToken);
    Alert.alert('Сохранено', 'Настройки сохранены на этом устройстве');
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
    <View style={styles.screen}>
      <Text style={styles.title}>AgroParts</Text>
      <Text style={styles.text}>
        Локальный каталог: {parts.length} поз. Обновите с сервера после синхронизации 1С.
      </Text>

      <Text style={styles.label}>URL API (AgroParts → 1С)</Text>
      <TextInput
        value={draftUrl}
        onChangeText={setDraftUrl}
        placeholder="http://192.168.1.10:8080"
        placeholderTextColor={colors.inkMuted}
        autoCapitalize="none"
        autoCorrect={false}
        style={styles.input}
      />

      <Text style={styles.label}>API Token</Text>
      <TextInput
        value={draftToken}
        onChangeText={setDraftToken}
        placeholder="необязательно"
        placeholderTextColor={colors.inkMuted}
        autoCapitalize="none"
        autoCorrect={false}
        secureTextEntry
        style={styles.input}
      />

      <Text style={styles.label}>OpenAI API Key (фото)</Text>
      <TextInput
        value={draftKey}
        onChangeText={setDraftKey}
        placeholder="sk-..."
        placeholderTextColor={colors.inkMuted}
        autoCapitalize="none"
        autoCorrect={false}
        secureTextEntry
        style={styles.input}
      />

      <Pressable style={styles.primary} onPress={() => void save()}>
        <Text style={styles.primaryText}>Сохранить</Text>
      </Pressable>
      <Pressable style={styles.secondary} onPress={() => void syncCatalog()} disabled={syncing}>
        <Text style={styles.secondaryText}>
          {syncing ? 'Обновление…' : 'Обновить каталог с сервера'}
        </Text>
      </Pressable>

      <View style={styles.box}>
        <Text style={styles.boxTitle}>Как подключить 1С</Text>
        <Text style={styles.text}>
          1. python sync_onec.py — номенклатура из 1С{'\n'}
          2. python api_server.py — шлюз :8080{'\n'}
          3. Укажите IP сервера выше{'\n'}
          4. «Обновить каталог» и оформляйте заявки
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bg,
    padding: spacing.md,
    gap: 12,
  },
  title: {
    fontFamily: 'DMSans_700Bold',
    fontSize: 22,
    color: colors.ink,
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
  box: {
    marginTop: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.line,
    gap: 8,
  },
  boxTitle: {
    fontFamily: 'DMSans_700Bold',
    color: colors.ink,
    fontSize: 16,
  },
});
