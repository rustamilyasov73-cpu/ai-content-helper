import { useMemo, useState } from 'react';
import { FlatList, StyleSheet, Text, TextInput, View } from 'react-native';
import { PartRow } from '../../src/components/PartRow';
import { searchParts, useParts } from '../../src/catalog';
import { go } from '../../src/nav';
import { colors, spacing } from '../../src/theme';

export default function SearchScreen() {
  const [query, setQuery] = useState('');
  const parts = useParts();
  const results = useMemo(() => searchParts(query), [query, parts]);

  return (
    <View style={styles.screen}>
      <View style={styles.searchBox}>
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Артикул, бренд, модель…"
          placeholderTextColor={colors.inkMuted}
          autoCapitalize="none"
          autoCorrect={false}
          style={styles.input}
        />
      </View>
      {!query.trim() ? (
        <Text style={styles.hint}>Например: RE507922 или фильтр John Deere</Text>
      ) : (
        <FlatList
          data={results}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <PartRow part={item} onPress={() => go(`/part/${item.id}`)} />
          )}
          ListEmptyComponent={<Text style={styles.hint}>Ничего не найдено</Text>}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  searchBox: {
    padding: spacing.md,
    backgroundColor: colors.bgDeep,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontFamily: 'DMSans_500Medium',
    fontSize: 16,
    color: colors.ink,
  },
  hint: {
    marginTop: 28,
    textAlign: 'center',
    color: colors.inkMuted,
    fontFamily: 'DMSans_400Regular',
    paddingHorizontal: spacing.lg,
  },
});
