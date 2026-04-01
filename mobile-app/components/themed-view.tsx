import { View, type ViewProps } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { useThemeColor } from '@/hooks/use-theme-color';

export type ThemedViewProps = ViewProps & {
  lightColor?: string;
  darkColor?: string;
  gradient?: boolean;
};

export function ThemedView({ style, lightColor, darkColor, gradient, ...otherProps }: ThemedViewProps) {
  const backgroundColor = useThemeColor({ light: lightColor, dark: darkColor }, 'background');
  const gradientStart = useThemeColor({}, 'gradientStart');
  const gradientEnd = useThemeColor({}, 'gradientEnd');

  if (gradient) {
    return (
      <LinearGradient
        colors={[gradientStart, gradientEnd]}
        style={[{ flex: 1 }, style]}
        {...otherProps}
      />
    );
  }

  return <View style={[{ backgroundColor }, style]} {...otherProps} />;
}
