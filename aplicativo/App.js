import Constants from 'expo-constants';
import { useState } from 'react';
import { ActivityIndicator, Pressable, StatusBar, StyleSheet, Text, View } from 'react-native';
import { WebView } from 'react-native-webview';

// CONFIGURACAO DO SITE: usa o .env ou detecta o computador que iniciou o Expo.
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

// AJUSTES POR PAGINA: estas mudancas afetam somente o conteudo dentro da WebView.
// MENU: remove o sublinhado dos links e mantem o destaque apenas na pagina ativa.
// LOGIN: usa a imagem disponivel no site quando a tela de login for carregada.
const pageAdjustments = `
(() => {
  const styleId = 'almoxarifado-app-adjustments';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = [
      '.navbar a { text-decoration: none !important; }',
      '.navbar button { text-decoration: none !important; }',
      '.navbar button.active { text-decoration: underline !important; text-decoration-thickness: 2px !important; text-underline-offset: 5px !important; }',
    ].join('');
    document.head.appendChild(style);
  }

  const loginImage = document.querySelector('img.imagem');
  if (loginImage) {
    loginImage.src = '/static/imagens/rogereleo.png';
  }

  return true;
})();
`;

// TELA PRINCIPAL DO EXPO GO: exibe o site, estado de carregamento e falhas de conexao.
export default function App() {
  const siteUrl = getSiteUrl();

  // ESTADO: permite repetir o carregamento sem fechar o aplicativo.
  const [reloadKey, setReloadKey] = useState(0);
  const [loadError, setLoadError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // ACAO DE TENTAR NOVAMENTE: recria a WebView para fazer outra requisicao.
  const retry = () => {
    setLoadError('');
    setIsLoading(true);
    setReloadKey((key) => key + 1);
  };

  // ERROS DE REDE: mostra uma mensagem e o endereco que o app tentou abrir.
  const showLoadError = (message) => {
    setIsLoading(false);
    setLoadError(message);
  };

  // INTERFACE: mostra erro, carregamento ou o site dentro da WebView.
  return (
    <View style={styles.container}>
      <StatusBar backgroundColor="#192A6B" barStyle="light-content" />
      {loadError ? (
        <View style={styles.errorContainer}>
          <Text style={styles.title}>Nao foi possivel conectar ao servidor</Text>
          <Text style={styles.message}>Endereco testado: {siteUrl}</Text>
          <Text style={styles.error}>{loadError}</Text>
          <Text style={styles.message}>
            Verifique se o servidor esta ligado e se o celular consegue acessar esse endereco.
          </Text>
          <Pressable accessibilityRole="button" onPress={retry} style={styles.retryButton}>
            <Text style={styles.retryButtonText}>Tentar novamente</Text>
          </Pressable>
        </View>
      ) : (
        <View style={styles.webViewContainer}>
          <WebView
            key={reloadKey}
            source={{ uri: `${siteUrl}/` }}
            originWhitelist={['*']}
            javaScriptEnabled
            domStorageEnabled
            injectedJavaScript={pageAdjustments}
            onMessage={() => {}}
            onLoadStart={() => setIsLoading(true)}
            onLoad={() => {
              setIsLoading(false);
              setLoadError('');
            }}
            onError={({ nativeEvent }) =>
              showLoadError(nativeEvent.description || 'Falha ao carregar a pagina.')
            }
            onHttpError={({ nativeEvent }) =>
              showLoadError(`O servidor respondeu com HTTP ${nativeEvent.statusCode}.`)
            }
            style={styles.webView}
          />
          {isLoading ? (
            <View pointerEvents="none" style={styles.loadingOverlay}>
              <ActivityIndicator color="#192A6B" size="large" />
              <Text style={styles.message}>Conectando ao servidor...</Text>
            </View>
          ) : null}
        </View>
      )}
    </View>
  );
}

// ESTILOS NATIVOS: organizam a WebView, o indicador e a tela de erro.
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFFFFF' },
  webViewContainer: { flex: 1 },
  webView: { flex: 1 },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    backgroundColor: '#FFFFFF',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 14,
  },
  title: { color: '#192A6B', fontSize: 20, fontWeight: '700', textAlign: 'center' },
  message: { color: '#344054', fontSize: 15, textAlign: 'center' },
  error: { color: '#B42318', fontSize: 14, textAlign: 'center' },
  retryButton: { backgroundColor: '#192A6B', borderRadius: 6, paddingHorizontal: 20, paddingVertical: 12 },
  retryButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '600' },
});
