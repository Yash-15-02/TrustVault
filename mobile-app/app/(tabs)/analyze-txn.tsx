import React, { useState } from 'react';
import { StyleSheet, TextInput, ScrollView, Alert, KeyboardAvoidingView, Platform, View, TouchableOpacity } from 'react-native';
import Animated, { FadeInUp, SlideInDown } from 'react-native-reanimated';

import { AnimatedButton } from '@/components/animated-button';
import { AnimatedCard } from '@/components/animated-card';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { AnalyzeResult } from '@/types/api';
import { useThemeColor } from '@/hooks/use-theme-color';

const API_BASE_URL = 'http://192.168.1.4:8000'; // Update to your computer's IP for mobile

export default function AnalyzeTransactionScreen() {
  const [amount, setAmount] = useState('');
  const [isNewReceiver, setIsNewReceiver] = useState(false);
  const [transactionsToday, setTransactionsToday] = useState('');
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [loading, setLoading] = useState(false);

  const textColor = useThemeColor({}, 'text');

  const analyzeTransaction = async () => {
    if (!amount || !transactionsToday) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: ' ',
          amount: Math.max(0.01, parseFloat(amount)),
          is_new_receiver: isNewReceiver ? 1 : 0,
          transactions_today: parseInt(transactionsToday),
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error('Failed to analyze transaction');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        Alert.alert('Error', 'Request timed out. Please check your connection and try again.');
      } else {
        Alert.alert('Error', error instanceof Error ? error.message : 'An unknown error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <ThemedView style={styles.inner}>
          <Animated.View entering={FadeInUp.duration(600)} style={styles.header}>
            <ThemedText type="title" style={styles.title}>
              Transaction Analysis
            </ThemedText>
            <ThemedText style={styles.description}>
              Enter transaction details to assess fraud risk
            </ThemedText>
          </Animated.View>

          <AnimatedCard delay={200}>
            <View style={styles.inputGroup}>
              <ThemedText style={styles.label}>Transaction Amount</ThemedText>
              <TextInput
                style={[styles.textInput, { color: textColor }]}
                placeholder="0.00"
                value={amount}
                onChangeText={setAmount}
                keyboardType="numeric"
                placeholderTextColor="#8E8E93"
              />
            </View>

            <View style={styles.inputGroup}>
              <ThemedText style={styles.label}>Transactions Today</ThemedText>
              <TextInput
                style={[styles.textInput, { color: textColor }]}
                placeholder="0"
                value={transactionsToday}
                onChangeText={setTransactionsToday}
                keyboardType="numeric"
                placeholderTextColor="#8E8E93"
              />
            </View>

            <View style={styles.switchGroup}>
              <ThemedText style={styles.label}>Is this a new receiver?</ThemedText>
              <TouchableOpacity
                style={[styles.switch, isNewReceiver && styles.switchActive]}
                onPress={() => setIsNewReceiver(!isNewReceiver)}
              >
                <View style={[styles.switchKnob, isNewReceiver && styles.switchKnobActive]} />
              </TouchableOpacity>
            </View>

            <AnimatedButton
              title="Analyze Transaction"
              onPress={analyzeTransaction}
              loading={loading}
            />
          </AnimatedCard>

          {result && (
            <Animated.View entering={SlideInDown.duration(500)} style={styles.resultContainer}>
              <AnimatedCard delay={0}>
                <ThemedText type="subtitle" style={styles.resultTitle}>
                  Analysis Result
                </ThemedText>
                <ThemedView style={[styles.riskBadge, { backgroundColor: getRiskColor(result.risk_level) }]}>
                  <ThemedText style={styles.riskText}>{result.risk_level}</ThemedText>
                </ThemedView>
                <ThemedText style={styles.recommendation}>
                  {result.recommendation}
                </ThemedText>
                <ThemedText style={styles.explanation}>
                  {result.explanation}
                </ThemedText>
              </AnimatedCard>
            </Animated.View>
          )}
        </ThemedView>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const getRiskColor = (riskLevel: string) => {
  switch (riskLevel.toLowerCase()) {
    case 'high':
      return '#FF3B30';
    case 'medium':
      return '#FF9500';
    case 'low':
      return '#34C759';
    default:
      return '#007AFF';
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  inner: {
    flex: 1,
    paddingTop: 60,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  description: {
    fontSize: 16,
    textAlign: 'center',
    opacity: 0.8,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#C6C6C8',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
  },
  switchGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  switch: {
    width: 50,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#C6C6C8',
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  switchActive: {
    backgroundColor: '#34C759',
  },
  switchKnob: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: 'white',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  switchKnobActive: {
    alignSelf: 'flex-end',
  },
  resultContainer: {
    marginTop: 20,
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 16,
    textAlign: 'center',
  },
  riskBadge: {
    alignSelf: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 16,
  },
  riskText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  recommendation: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
  },
  explanation: {
    fontSize: 14,
    lineHeight: 20,
  },
});