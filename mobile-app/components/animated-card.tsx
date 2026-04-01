import React from 'react';
import { StyleSheet } from 'react-native';
import Animated, { FadeInUp } from 'react-native-reanimated';

import { ThemedView } from '@/components/themed-view';

interface AnimatedCardProps {
  children: React.ReactNode;
  delay?: number;
}

export function AnimatedCard({ children, delay = 0 }: AnimatedCardProps) {
  return (
    <Animated.View
      entering={FadeInUp.delay(delay).duration(600)}
      style={styles.card}
    >
      <ThemedView style={styles.inner}>
        {children}
      </ThemedView>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    margin: 16,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  inner: {
    padding: 20,
    borderRadius: 16,
  },
});