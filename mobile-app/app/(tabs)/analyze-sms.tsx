import React, { useState } from 'react';
import { StyleSheet, TextInput, ScrollView, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import Animated, { FadeInUp, SlideInDown } from 'react-native-reanimated';

import { AnimatedButton } from '@/components/animated-button';
import { AnimatedCard } from '@/components/animated-card';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { AnalyzeResult } from '@/types/api';
import { useThemeColor } from '@/hooks/use-theme-color';

const API_BASE_URL = 'http://192.168.1.4:8000'; // Update to your computer's IP for mobile

export default function AnalyzeSMSScreen() {
  const [smsText, setSmsText] = useState('');
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [loading, setLoading] = useState(false);

  const textColor = useThemeColor({}, 'text');

  const analyzeSMS = async () => {
    if (!smsText.trim()) {
      Alert.alert('Error', 'Please enter SMS text');
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
          message: smsText,
          amount: 0.01,
          is_new_receiver: 0,
          transactions_today: 0,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error('Failed to analyze SMS');
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
              SMS Analysis
            </ThemedText>
            <ThemedText style={styles.description}>
              Paste your SMS message below to check for potential scams
            </ThemedText>
          </Animated.View>

          <AnimatedCard delay={200}>
            <TextInput
              style={[styles.textInput, { color: textColor }]}
              placeholder="Enter SMS text here..."
              value={smsText}
              onChangeText={setSmsText}
              multiline
              numberOfLines={6}
              placeholderTextColor="#8E8E93"
            />
            <AnimatedButton
              title="Analyze SMS"
              onPress={analyzeSMS}
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
  textInput: {
    borderWidth: 1,
    borderColor: '#C6C6C8',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    fontSize: 16,
    minHeight: 120,
    textAlignVertical: 'top',
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
  explanation: {
    fontSize: 14,
    lineHeight: 20,
  },
});