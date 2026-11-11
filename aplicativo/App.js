import { WebView } from 'react-native-webview';
import { StatusBar, StyleSheet, View } from 'react-native';

const BASE_URL = 'http://10.154.20.87:5000';

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar backgroundColor="#192A6B" barStyle="light-content" />
      <WebView
        source={{ uri: `${BASE_URL}/` }}
        javaScriptEnabled
        domStorageEnabled
        style={styles.webView}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  webView: { flex: 1 },
});
