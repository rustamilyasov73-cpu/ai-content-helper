import * as ImagePicker from 'expo-image-picker';
import { Image } from 'expo-image';
import { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { PartRow } from '../../src/components/PartRow';
import { matchBySkuCandidates, useParts } from '../../src/catalog';
import { useSettings } from '../../src/context/SettingsContext';
import { go } from '../../src/nav';
import { colors, spacing } from '../../src/theme';
import type { Part, PhotoRecognition } from '../../src/types';
import { recognizePartPhoto } from '../../src/vision';

export default function PhotoScreen() {
  useParts();
  const { apiKey } = useSettings();
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PhotoRecognition | null>(null);
  const [matches, setMatches] = useState<Part[]>([]);
  const [searched, setSearched] = useState(false);

  async function pick(fromCamera: boolean) {
    const permission = fromCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setResult({
        rawText: '',
        candidates: [],
        brand: '',
        model: '',
        notes: '',
        error: 'Нужен доступ к камере/галерее',
      });
      return;
    }

    const picked = fromCamera
      ? await ImagePicker.launchCameraAsync({
          quality: 0.7,
          base64: true,
        })
      : await ImagePicker.launchImageLibraryAsync({
          quality: 0.7,
          base64: true,
        });

    if (picked.canceled || !picked.assets?.[0]) return;
    const asset = picked.assets[0];
    setPreview(asset.uri);
    setLoading(true);
    setResult(null);
    setMatches([]);
    setSearched(false);

    const mime = asset.mimeType || 'image/jpeg';
    const base64 = asset.base64;
    if (!base64) {
      setLoading(false);
      setResult({
        rawText: '',
        candidates: [],
        brand: '',
        model: '',
        notes: '',
        error: 'Не удалось прочитать изображение',
      });
      return;
    }

    const recognition = await recognizePartPhoto(base64, mime, apiKey);
    setResult(recognition);
    if (!recognition.error && recognition.candidates.length) {
      setMatches(matchBySkuCandidates(recognition.candidates));
      setSearched(true);
    } else if (!recognition.error) {
      setSearched(true);
    }
    setLoading(false);
  }

  return (
    <View style={styles.screen}>
      <View style={styles.intro}>
        <Text style={styles.title}>Снимите бирку или шильдик</Text>
        <Text style={styles.sub}>
          Приложение распознает артикул и найдёт деталь в каталоге
        </Text>
        {!apiKey ? (
          <Text style={styles.warn}>Сначала укажите OpenAI API ключ во вкладке Настройки</Text>
        ) : null}
      </View>

      <View style={styles.actions}>
        <Pressable style={styles.primary} onPress={() => pick(true)} disabled={loading}>
          <Text style={styles.primaryText}>Камера</Text>
        </Pressable>
        <Pressable style={styles.secondary} onPress={() => pick(false)} disabled={loading}>
          <Text style={styles.secondaryText}>Галерея</Text>
        </Pressable>
      </View>

      {preview ? <Image source={{ uri: preview }} style={styles.preview} contentFit="cover" /> : null}
      {loading ? (
        <View style={styles.loading}>
          <ActivityIndicator color={colors.brand} />
          <Text style={styles.loadingText}>Распознаём артикул…</Text>
        </View>
      ) : null}

      {result?.error ? <Text style={styles.error}>{result.error}</Text> : null}

      {result && !result.error ? (
        <View style={styles.resultBox}>
          {result.candidates.length ? (
            <Text style={styles.resultTitle}>Найденные коды: {result.candidates.join(', ')}</Text>
          ) : (
            <Text style={styles.resultTitle}>Артикулы не распознаны</Text>
          )}
          {result.notes ? <Text style={styles.resultNotes}>{result.notes}</Text> : null}
          {result.brand || result.model ? (
            <Text style={styles.resultNotes}>
              {[result.brand, result.model].filter(Boolean).join(' · ')}
            </Text>
          ) : null}
        </View>
      ) : null}

      <FlatList
        style={styles.list}
        data={matches}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <PartRow part={item} onPress={() => go(`/part/${item.id}`)} />
        )}
        ListHeaderComponent={
          matches.length ? <Text style={styles.listHeader}>Совпадения в каталоге</Text> : null
        }
        ListEmptyComponent={
          searched && result && !result.error && result.candidates.length ? (
            <Text style={styles.empty}>
              Коды распознаны, но в каталоге совпадений нет. Обновите каталог с сервера или
              уточните артикул в Поиске.
            </Text>
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  intro: {
    padding: spacing.md,
    gap: 6,
    backgroundColor: colors.bgDeep,
  },
  title: {
    fontFamily: 'DMSans_700Bold',
    fontSize: 20,
    color: colors.ink,
  },
  sub: {
    fontFamily: 'DMSans_400Regular',
    fontSize: 14,
    color: colors.inkMuted,
  },
  warn: {
    marginTop: 4,
    fontFamily: 'DMSans_500Medium',
    color: colors.accent,
    fontSize: 13,
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
    padding: spacing.md,
  },
  primary: {
    flex: 1,
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
    flex: 1,
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
    fontSize: 16,
  },
  preview: {
    height: 180,
    marginHorizontal: spacing.md,
    borderRadius: 12,
    backgroundColor: colors.line,
  },
  loading: {
    flexDirection: 'row',
    gap: 10,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.md,
  },
  loadingText: {
    fontFamily: 'DMSans_500Medium',
    color: colors.inkMuted,
  },
  error: {
    marginHorizontal: spacing.md,
    color: colors.danger,
    fontFamily: 'DMSans_500Medium',
  },
  resultBox: {
    margin: spacing.md,
    padding: spacing.md,
    backgroundColor: colors.accentSoft,
    borderRadius: 10,
    gap: 4,
  },
  resultTitle: {
    fontFamily: 'DMSans_700Bold',
    color: colors.ink,
    fontSize: 15,
  },
  resultNotes: {
    fontFamily: 'DMSans_400Regular',
    color: colors.inkMuted,
    fontSize: 13,
  },
  list: { flex: 1 },
  listHeader: {
    paddingHorizontal: spacing.md,
    paddingBottom: 6,
    fontFamily: 'DMSans_600SemiBold',
    color: colors.ink,
  },
  empty: {
    marginHorizontal: spacing.md,
    marginTop: 8,
    fontFamily: 'DMSans_400Regular',
    color: colors.inkMuted,
    lineHeight: 20,
  },
});
