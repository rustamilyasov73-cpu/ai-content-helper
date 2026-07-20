import { useEffect, useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useSettings } from '../../src/context/SettingsContext';
import { colors, spacing } from '../../src/theme';

export default function SettingsScreen() {
  const { apiKey, setApiKey, ready } = useSettings();
  const [draft, setDraft] = useState('');

  useEffect(() => {
    if (ready) setDraft(apiKey);
  }, [apiKey, ready]);

  async function save() {
    await setApiKey(draft);
    Alert.alert('Сохранено', 'Ключ сохранён на этом устройстве');
  }

  return (
    <View style={styles.screen}>
      <Text style={styles.title}>AgroParts на телефоне</Text>
      <Text style={styles.text}>
        Каталог и корзина работают офлайн. Для распознавания бирок по фото нужен OpenAI API ключ
        (модель с vision, например gpt-4o-mini).
      </Text>

      <Text style={styles.label}>OpenAI API Key</Text>
      <TextInput
        value={draft}
        onChangeText={setDraft}
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
        <Text style={styles.boxTitle}>Как открыть на телефоне</Text>
        <Text style={styles.text}>
          1. Установите Expo Go{'\n'}
          2. На компьютере: cd mobile && npx expo start{'\n'}
          3. Отсканируйте QR-код камерой / Expo Go
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
