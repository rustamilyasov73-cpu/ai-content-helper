import { useMemo, useState } from 'react';
import { FlatList, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { PartRow } from '../../src/components/PartRow';
import {
  brands,
  byBrand,
  byCategory,
  categories,
  useParts,
} from '../../src/catalog';
import { go } from '../../src/nav';
import { colors, spacing } from '../../src/theme';

type Filter =
  | { type: 'all' }
  | { type: 'category'; key: string; label: string }
  | { type: 'brand'; name: string };

export default function CatalogScreen() {
  const [filter, setFilter] = useState<Filter>({ type: 'all' });
  const all = useParts();
  const cats = useMemo(() => categories(), [all]);
  const brandList = useMemo(() => brands(), [all]);

  const parts = useMemo(() => {
    if (filter.type === 'category') return byCategory(filter.key);
    if (filter.type === 'brand') return byBrand(filter.name);
    return all;
  }, [filter, all]);

  return (
    <View style={styles.screen}>
      <View style={styles.hero}>
        <Text style={styles.brand}>AgroParts</Text>
        <Text style={styles.heroText}>Запчасти для тракторов и комбайнов</Text>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
        <Chip
          label="Все"
          active={filter.type === 'all'}
          onPress={() => setFilter({ type: 'all' })}
        />
        {cats.map((c) => (
          <Chip
            key={c.key}
            label={`${c.label} (${c.count})`}
            active={filter.type === 'category' && filter.key === c.key}
            onPress={() => setFilter({ type: 'category', key: c.key, label: c.label })}
          />
        ))}
        {brandList.map((b) => (
          <Chip
            key={b.name}
            label={b.name}
            active={filter.type === 'brand' && filter.name === b.name}
            onPress={() => setFilter({ type: 'brand', name: b.name })}
          />
        ))}
      </ScrollView>

      <FlatList
        data={parts}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <PartRow part={item} onPress={() => go(`/part/${item.id}`)} />
        )}
        ListEmptyComponent={<Text style={styles.empty}>Ничего не найдено</Text>}
      />
    </View>
  );
}

function Chip({
  label,
  active,
  onPress,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={[styles.chip, active && styles.chipActive]}>
      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  hero: {
    backgroundColor: colors.brand,
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.md,
    paddingTop: spacing.sm,
    gap: 4,
  },
  brand: {
    color: colors.white,
    fontFamily: 'DMSans_700Bold',
    fontSize: 28,
    letterSpacing: -0.5,
  },
  heroText: {
    color: '#D7E8DE',
    fontFamily: 'DMSans_400Regular',
    fontSize: 14,
  },
  chips: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    gap: 8,
    backgroundColor: colors.bgDeep,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
  },
  chipActive: {
    backgroundColor: colors.brand,
    borderColor: colors.brand,
  },
  chipText: {
    fontFamily: 'DMSans_500Medium',
    color: colors.ink,
    fontSize: 13,
  },
  chipTextActive: { color: colors.white },
  empty: {
    textAlign: 'center',
    marginTop: 40,
    color: colors.inkMuted,
    fontFamily: 'DMSans_400Regular',
  },
});
