import FontAwesome from '@expo/vector-icons/FontAwesome';
import { Tabs } from 'expo-router';
import type { ComponentProps } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { useCart } from '../../src/context/CartContext';
import { go } from '../../src/nav';
import { colors } from '../../src/theme';

type TabItem = {
  name: 'index' | 'search' | 'photo' | 'cart' | 'settings';
  title: string;
  href: string;
  icon: ComponentProps<typeof FontAwesome>['name'];
};

const TABS: TabItem[] = [
  { name: 'index', title: 'Каталог', href: '/', icon: 'th-large' },
  { name: 'search', title: 'Поиск', href: '/search', icon: 'search' },
  { name: 'photo', title: 'Фото', href: '/photo', icon: 'camera' },
  { name: 'cart', title: 'Корзина', href: '/cart', icon: 'shopping-cart' },
  { name: 'settings', title: 'Настройки', href: '/settings', icon: 'cog' },
];

function CustomTabBar({ state }: { state: { index: number; routes: Array<{ name: string }> } }) {
  const { totalQty } = useCart();
  return (
    <View style={styles.bar}>
      {TABS.map((tab, index) => {
        const active = state.routes[state.index]?.name === tab.name || state.index === index;
        return (
          <Pressable
            key={tab.name}
            onPress={() => go(tab.href)}
            style={styles.item}
            accessibilityRole="button"
            accessibilityState={{ selected: active }}
          >
            <View>
              <FontAwesome
                name={tab.icon}
                size={20}
                color={active ? colors.brand : colors.inkMuted}
              />
              {tab.name === 'cart' && totalQty > 0 ? (
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{totalQty}</Text>
                </View>
              ) : null}
            </View>
            <Text style={[styles.label, active && styles.labelActive]}>{tab.title}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export default function TabLayout() {
  return (
    <Tabs
      tabBar={(props) => <CustomTabBar state={props.state} />}
      screenOptions={{
        headerStyle: { backgroundColor: colors.brand },
        headerTintColor: colors.white,
        headerTitleStyle: { fontFamily: 'DMSans_700Bold', fontSize: 18 },
        sceneStyle: Platform.OS === 'web' ? { flex: 1 } : undefined,
      }}
    >
      {TABS.map((tab) => (
        <Tabs.Screen key={tab.name} name={tab.name} options={{ title: tab.title }} />
      ))}
    </Tabs>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderTopColor: colors.line,
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingBottom: Platform.OS === 'web' ? 8 : 6,
    paddingTop: 8,
    zIndex: 20,
  },
  item: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
    paddingVertical: 4,
  },
  label: {
    fontFamily: 'DMSans_500Medium',
    fontSize: 11,
    color: colors.inkMuted,
  },
  labelActive: { color: colors.brand },
  badge: {
    position: 'absolute',
    top: -6,
    right: -10,
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 3,
  },
  badgeText: {
    color: colors.white,
    fontSize: 10,
    fontFamily: 'DMSans_700Bold',
  },
});
