import { useEffect, useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useSettings } from '../../src/context/SettingsContext';
import { colors, spacing } from '../../src/theme';

export default function SettingsScreen() {
  const { apiKey, apiBaseUrl, apiToken, setApiKey, setApiBaseUrl, setApiToken, ready } =
    useSettings();
  const [draftKey, setDraftKey] = useState('');
  const [draftUrl, setDraftUrl] = useState('');
  const [draftToken, setDraftToken] = useState('');

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

  return (
    <View style={styles.screen}>
      <Text style={styles.title}>AgroParts на телефоне</Text>
      <Text style={styles.text}>
        Каталог и корзина работают офлайн. Для распознавания бирок — OpenAI ключ. Для отправки
        заявок в 1С:Бухгалтерия — URL API-шлюза AgroParts.
      </Text>

      <Text style={styles.label}>URL API (1С через AgroParts)</Text>
      <TextInput
        value={draftUrl}
        onChangeText={setDraftUrl}
        placeholder="http://192.168.1.10:8080"
        placeholderTextColor={colors.inkMuted}
        autoCapitalize="none"
        autoCorrect={false}
        style={styles.input}
      />

      <Text style={styles.label}>API Token (если задан на сервере)</Text>
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

      <Text style={styles.label}>OpenAI API Key</Text>
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
      <Pressable style={styles.primary} onPress={save}>
        <Text style={styles.primaryText}>Сохранить</Text>
      </Pressable>

      <View style={styles.box}>
        <Text style={styles.boxTitle}>1С:Бухгалтерия</Text>
        <Text style={styles.text}>
          1. На сервере: python api_server.py{'\n'}
          2. В .env включите ONEC_ENABLED и ONEC_BASE_URL{'\n'}
          3. Укажите здесь IP сервера с портом 8080{'\n'}
          4. Заявки из корзины уйдут в 1С
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
