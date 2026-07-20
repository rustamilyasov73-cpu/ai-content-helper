import { useState } from 'react';
import {
  Alert,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { QtyControls } from '../../src/components/QtyControls';
import { formatPrice, getPart } from '../../src/catalog';
import { useCart } from '../../src/context/CartContext';
import { go } from '../../src/nav';
import { colors, spacing } from '../../src/theme';

export default function CartScreen() {
  const { items, setQty, remove, totalPrice, placeOrder, orders } = useCart();
  const [phone, setPhone] = useState('');
  const [comment, setComment] = useState('');

  function submit() {
    const order = placeOrder(phone, comment);
    if (!order) {
      Alert.alert('Заявка', 'Добавьте товары и укажите телефон');
      return;
    }
    Alert.alert('Заявка отправлена', `№ ${order.id}\nСумма ${formatPrice(order.total)}`);
    setPhone('');
    setComment('');
  }

  return (
    <View style={styles.screen}>
      <FlatList
        data={items}
        keyExtractor={(item) => item.partId}
        ListHeaderComponent={
          <Text style={styles.section}>
            {items.length ? 'Позиции' : 'Корзина пуста — добавьте детали из каталога'}
          </Text>
        }
        renderItem={({ item }) => {
          const part = getPart(item.partId);
          if (!part) return null;
          return (
            <View style={styles.row}>
              <Pressable style={{ flex: 1 }} onPress={() => go(`/part/${part.id}`)}>
                <Text style={styles.sku}>{part.sku}</Text>
                <Text style={styles.name}>{part.name}</Text>
                <Text style={styles.price}>{formatPrice(part.price * item.qty)}</Text>
              </Pressable>
              <View style={styles.controls}>
                <QtyControls
                  qty={item.qty}
                  onMinus={() => setQty(part.id, item.qty - 1)}
                  onPlus={() => setQty(part.id, item.qty + 1)}
                />
                <Pressable onPress={() => remove(part.id)}>
                  <Text style={styles.remove}>Удалить</Text>
                </Pressable>
              </View>
            </View>
          );
        }}
        ListFooterComponent={
          <View style={styles.footer}>
            {items.length ? (
              <>
                <Text style={styles.total}>Итого: {formatPrice(totalPrice)}</Text>
                <TextInput
                  value={phone}
                  onChangeText={setPhone}
                  placeholder="Телефон для связи"
                  placeholderTextColor={colors.inkMuted}
                  keyboardType="phone-pad"
                  style={styles.input}
                />
                <TextInput
                  value={comment}
                  onChangeText={setComment}
                  placeholder="Комментарий (модель техники, срочность…)"
                  placeholderTextColor={colors.inkMuted}
                  multiline
                  style={[styles.input, styles.comment]}
                />
                <Pressable style={styles.primary} onPress={submit}>
                  <Text style={styles.primaryText}>Оформить заявку</Text>
                </Pressable>
              </>
            ) : null}

            {orders.length ? (
              <View style={styles.orders}>
                <Text style={styles.section}>Последние заявки</Text>
                {orders.slice(0, 5).map((order) => (
                  <View key={order.id} style={styles.orderCard}>
                    <Text style={styles.orderId}>{order.id}</Text>
                    <Text style={styles.orderMeta}>
                      {new Date(order.createdAt).toLocaleString('ru-RU')} · {order.phone}
                    </Text>
                    <Text style={styles.orderMeta}>
                      {order.items.length} поз. · {formatPrice(order.total)}
                    </Text>
                  </View>
                ))}
              </View>
            ) : null}
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  section: {
    padding: spacing.md,
    fontFamily: 'DMSans_600SemiBold',
    color: colors.inkMuted,
  },
  row: {
    backgroundColor: colors.surface,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
    padding: spacing.md,
    flexDirection: 'row',
    gap: spacing.md,
    alignItems: 'center',
  },
  sku: {
    fontFamily: 'DMSans_700Bold',
    color: colors.brand,
    fontSize: 13,
  },
  name: {
    fontFamily: 'DMSans_600SemiBold',
    color: colors.ink,
    fontSize: 15,
    marginTop: 2,
  },
  price: {
    marginTop: 4,
    fontFamily: 'DMSans_700Bold',
    color: colors.ink,
  },
  controls: { alignItems: 'center', gap: 8 },
  remove: {
    color: colors.danger,
    fontFamily: 'DMSans_500Medium',
    fontSize: 12,
  },
  footer: { padding: spacing.md, gap: 12 },
  total: {
    fontFamily: 'DMSans_700Bold',
    fontSize: 22,
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
    fontSize: 16,
    color: colors.ink,
  },
  comment: { minHeight: 80, textAlignVertical: 'top' },
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
  orders: { marginTop: spacing.md, gap: 8 },
  orderCard: {
    backgroundColor: colors.surface,
    borderRadius: 10,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.line,
    gap: 2,
  },
  orderId: { fontFamily: 'DMSans_700Bold', color: colors.ink },
  orderMeta: { fontFamily: 'DMSans_400Regular', color: colors.inkMuted, fontSize: 13 },
});
