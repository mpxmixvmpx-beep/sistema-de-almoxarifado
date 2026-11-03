import Constants from 'expo-constants';
import { StatusBar, StyleSheet, View } from 'react-native';
import { WebView } from 'react-native-webview';

const getSiteUrl = () => {
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL.replace(/\/+$/, '');
  }

  const location = typeof window !== 'undefined' ? window.location : undefined;
  if (location?.protocol && location.hostname) {
    return `${location.protocol}//${location.hostname}:5000`;
  }

  const hostUri = Constants.expoConfig?.hostUri;
  const host = hostUri?.match(/^(\[[^\]]+\]|[^:]+)(?::\d+)?$/)?.[1];
  return `http://${host || '127.0.0.1'}:5000`;
};

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar backgroundColor="#192A6B" barStyle="light-content" />
      <WebView
        source={{ uri: `${getSiteUrl()}/` }}
        originWhitelist={['*']}
        javaScriptEnabled
        domStorageEnabled
        style={styles.webView}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  webView: { flex: 1 },
});
