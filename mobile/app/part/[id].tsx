import { Stack, useLocalSearchParams } from 'expo-router';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { categoryLabel, formatPrice, getPart } from '../../src/catalog';
import { useCart } from '../../src/context/CartContext';
import { go } from '../../src/nav';
import { colors, spacing } from '../../src/theme';

export default function PartScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const part = getPart(String(id));
  const { add } = useCart();

  if (!part) {
    return (
      <View style={styles.screen}>
        <Text style={styles.missing}>Деталь не найдена</Text>
      </View>
    );
  }

  function onAdd() {
    if (!part) return;
    if (part.stock <= 0) {
      Alert.alert('Нет в наличии');
      return;
    }
    add(part.id, 1);
    Alert.alert('В корзине', part.name, [
      { text: 'Продолжить' },
      { text: 'В корзину', onPress: () => go('/cart') },
    ]);
  }

  return (
    <>
      <Stack.Screen options={{ title: part.sku }} />
      <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
        <Text style={styles.sku}>{part.sku}</Text>
        <Text style={styles.name}>{part.name}</Text>
        <Text style={styles.meta}>
          {part.brand} · {categoryLabel(part.category)}
        </Text>
        <Text style={styles.price}>{formatPrice(part.price)} / {part.unit}</Text>
        <Text style={[styles.stock, part.stock > 0 ? styles.ok : styles.bad]}>
          {part.stock > 0 ? `В наличии: ${part.stock} ${part.unit}` : 'Нет в наличии'}
        </Text>
        <Text style={styles.label}>Совместимость</Text>
        <Text style={styles.body}>{part.compatible.join(', ')}</Text>
        <Text style={styles.label}>Описание</Text>
        <Text style={styles.body}>{part.description}</Text>
        <Pressable style={[styles.primary, part.stock <= 0 && styles.disabled]} onPress={onAdd}>
          <Text style={styles.primaryText}>В корзину</Text>
        </Pressable>
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, gap: 8 },
  missing: {
    marginTop: 40,
    textAlign: 'center',
    fontFamily: 'DMSans_500Medium',
    color: colors.inkMuted,
  },
  sku: {
    fontFamily: 'DMSans_700Bold',
    color: colors.brand,
    fontSize: 14,
    letterSpacing: 0.5,
  },
  name: {
    fontFamily: 'DMSans_700Bold',
    fontSize: 26,
    color: colors.ink,
    letterSpacing: -0.3,
  },
  meta: {
    fontFamily: 'DMSans_400Regular',
    color: colors.inkMuted,
    fontSize: 15,
  },
  price: {
    marginTop: 8,
    fontFamily: 'DMSans_700Bold',
    fontSize: 24,
    color: colors.ink,
  },
  stock: { fontFamily: 'DMSans_600SemiBold', fontSize: 14 },
  ok: { color: colors.ok },
  bad: { color: colors.danger },
  label: {
    marginTop: 14,
    fontFamily: 'DMSans_700Bold',
    color: colors.ink,
    fontSize: 13,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  body: {
    fontFamily: 'DMSans_400Regular',
    color: colors.ink,
    fontSize: 16,
    lineHeight: 22,
  },
  primary: {
    marginTop: spacing.lg,
    backgroundColor: colors.brand,
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
  },
  disabled: { opacity: 0.45 },
  primaryText: {
    color: colors.white,
    fontFamily: 'DMSans_700Bold',
    fontSize: 17,
  },
});
