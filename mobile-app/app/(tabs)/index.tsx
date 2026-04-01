import React from 'react';
import { StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import Animated, { FadeInDown } from 'react-native-reanimated';

import { AnimatedCard } from '@/components/animated-card';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';

export default function HomeScreen() {
  const router = useRouter();

  return (
    <ThemedView style={styles.container} gradient>
      <Animated.View entering={FadeInDown.duration(800)} style={styles.header}>
        <ThemedText type="title" style={styles.title}>
          TrustVault AI
        </ThemedText>
        <ThemedText style={styles.subtitle}>
          Secure your transactions with AI-powered fraud detection
        </ThemedText>
      </Animated.View>

      <AnimatedCard delay={200}>
        <TouchableOpacity
          style={styles.cardContent}
          onPress={() => router.push('/analyze-sms')}
        >
          <IconSymbol name="message.fill" size={48} color="#007AFF" />
          <ThemedText type="subtitle" style={styles.cardTitle}>
            Analyze SMS
          </ThemedText>
          <ThemedText style={styles.cardDescription}>
            Check SMS messages for potential scams and fraud
          </ThemedText>
        </TouchableOpacity>
      </AnimatedCard>

      <AnimatedCard delay={400}>
        <TouchableOpacity
          style={styles.cardContent}
          onPress={() => router.push('/analyze-txn')}
        >
          <IconSymbol name="creditcard.fill" size={48} color="#007AFF" />
          <ThemedText type="subtitle" style={styles.cardTitle}>
            Analyze Transaction
          </ThemedText>
          <ThemedText style={styles.cardDescription}>
            Evaluate transaction details for fraud risk
          </ThemedText>
        </TouchableOpacity>
      </AnimatedCard>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 60,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    textAlign: 'center',
    opacity: 0.8,
  },
  cardContent: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginTop: 12,
    marginBottom: 8,
  },
  cardDescription: {
    fontSize: 14,
    textAlign: 'center',
    opacity: 0.7,
  },
});