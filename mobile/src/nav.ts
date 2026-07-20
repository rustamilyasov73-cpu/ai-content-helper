import { Platform } from 'react-native';
import { router, type Href } from 'expo-router';

/** Надёжный переход: на вебе полный reload (обходит баг static export + tabs). */
export function go(href: string) {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    window.location.assign(href);
    return;
  }
  router.push(href as Href);
}
