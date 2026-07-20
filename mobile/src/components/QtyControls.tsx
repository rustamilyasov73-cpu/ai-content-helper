import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors } from '../theme';

type Props = {
  qty: number;
  onMinus: () => void;
  onPlus: () => void;
};

export function QtyControls({ qty, onMinus, onPlus }: Props) {
  return (
    <View style={styles.wrap}>
      <Pressable onPress={onMinus} style={styles.btn} hitSlop={8}>
        <Text style={styles.btnText}>−</Text>
      </Pressable>
      <Text style={styles.qty}>{qty}</Text>
      <Pressable onPress={onPlus} style={styles.btn} hitSlop={8}>
        <Text style={styles.btnText}>+</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  btn: {
    width: 34,
    height: 34,
    borderRadius: 8,
    backgroundColor: colors.brand,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnText: {
    color: colors.white,
    fontSize: 20,
    fontFamily: 'DMSans_700Bold',
    lineHeight: 22,
  },
  qty: {
    minWidth: 24,
    textAlign: 'center',
    fontFamily: 'DMSans_700Bold',
    fontSize: 16,
    color: colors.ink,
  },
});
