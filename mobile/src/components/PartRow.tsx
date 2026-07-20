import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { categoryLabel, formatPrice } from '../catalog';
import { colors, spacing } from '../theme';
import type { Part } from '../types';

type Props = {
  part: Part;
  onPress: () => void;
  right?: ReactNode;
};

export function PartRow({ part, onPress, right }: Props) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.row, pressed && styles.pressed]}>
      <View style={styles.main}>
        <Text style={styles.sku}>{part.sku}</Text>
        <Text style={styles.name}>{part.name}</Text>
        <Text style={styles.meta}>
          {part.brand} · {categoryLabel(part.category)}
        </Text>
        <View style={styles.footer}>
          <Text style={styles.price}>{formatPrice(part.price)}</Text>
          <Text style={[styles.stock, part.stock > 0 ? styles.inStock : styles.outStock]}>
            {part.stock > 0 ? `${part.stock} ${part.unit}` : 'нет'}
          </Text>
        </View>
      </View>
      {right}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    backgroundColor: colors.surface,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    flexDirection: 'row',
    gap: spacing.sm,
    alignItems: 'center',
  },
  pressed: { opacity: 0.85 },
  main: { flex: 1, gap: 3 },
  sku: {
    color: colors.brand,
    fontFamily: 'DMSans_700Bold',
    fontSize: 13,
    letterSpacing: 0.4,
  },
  name: {
    color: colors.ink,
    fontFamily: 'DMSans_600SemiBold',
    fontSize: 16,
  },
  meta: {
    color: colors.inkMuted,
    fontFamily: 'DMSans_400Regular',
    fontSize: 13,
  },
  footer: {
    marginTop: 4,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  price: {
    color: colors.ink,
    fontFamily: 'DMSans_700Bold',
    fontSize: 15,
  },
  stock: {
    fontFamily: 'DMSans_500Medium',
    fontSize: 12,
  },
  inStock: { color: colors.ok },
  outStock: { color: colors.danger },
});
