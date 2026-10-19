import React, { useMemo, useState } from 'react';
import {
  Alert,
  Image,
  ImageBackground,
  Modal,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

const NAVY = '#192A6B';
const TABLE_NAVY = '#0A1F44';
const GOLD = '#F59E0B';

const apiBaseUrl = () =>
  process.env.EXPO_PUBLIC_API_URL ||
  (typeof window !== 'undefined'
    ? `${window.location.protocol}//${window.location.hostname}:5000`
    : 'http://127.0.0.1:5000');

export default function App() {
  const [screen, setScreen] = useState('login');
  const [currentUser, setCurrentUser] = useState(null);
  const [items, setItems] = useState([]);
  const [users, setUsers] = useState([]);
  const [login, setLogin] = useState({ nome: '', senha: '' });
  const [loginError, setLoginError] = useState('');
  const [notice, setNotice] = useState('');
  const [previewImage, setPreviewImage] = useState(null);
  const [previewImageError, setPreviewImageError] = useState(false);
  const [cadastro, setCadastro] = useState({
    nome: '',
    descricao: '',
    qtd: '',
    preco: '',
    imagem: '',
  });
  const [movimentacao, setMovimentacao] = useState({
    itemId: null,
    tipo: 'entrada',
    quantidade: '1',
  });
  const [novoUsuario, setNovoUsuario] = useState({ tipo: 'user', nome: '', senha: '' });
  const [csvInput, setCsvInput] = useState('');
  const [csvOutput, setCsvOutput] = useState('');

  const request = async (path, options = {}) => {
    const baseUrl = apiBaseUrl();
    let response;
    try {
      response = await fetch(`${baseUrl}${path}`, {
        credentials: 'include',
        ...options,
        headers: {
          ...(options.body && typeof options.body !== 'string'
            ? { 'Content-Type': 'application/json' }
            : {}),
          ...options.headers,
        },
        body:
          options.body && typeof options.body !== 'string'
            ? JSON.stringify(options.body)
            : options.body,
      });
    } catch (error) {
      throw new Error(
        `Não foi possível conectar a ${baseUrl}. Confira o servidor e a rede do aparelho.`,
      );
    }

    const contentType = response.headers.get('content-type') || '';
    const result = contentType.includes('application/json')
      ? await response.json()
      : await response.text();
    if (!response.ok) {
      throw new Error(
        (result && result.erro) || `Erro na comunicação com o servidor (${response.status}).`,
      );
    }
    return result;
  };

  const loadItems = async () => {
    const data = await request('/api/itens');
    setItems(data);
    return data;
  };

  const loadUsers = async () => {
    setUsers(await request('/api/usuarios'));
  };

  const handleLogin = async () => {
    setLoginError('');
    try {
      const usuario = await request('/api/login', { method: 'POST', body: login });
      setCurrentUser(usuario);
      setItems(await request('/api/itens'));
      if (usuario.tipo === 'admin') await loadUsers();
      setScreen('home');
    } catch (error) {
      setCurrentUser(null);
      setLoginError(error.message);
    }
  };

  const handleLogout = async () => {
    try {
      await request('/api/logout', { method: 'POST' });
      setCurrentUser(null);
      setItems([]);
      setUsers([]);
      setScreen('login');
    } catch (error) {
      Alert.alert('Não foi possível sair', error.message);
    }
  };

  const handleCadastro = async () => {
    const quantidade = Number(cadastro.qtd);
    const preco = Number(cadastro.preco.replace(',', '.'));
    if (!cadastro.nome.trim() || !cadastro.descricao.trim()) {
      Alert.alert('Dados incompletos', 'Informe o nome e a descrição do item.');
      return;
    }
    if (!Number.isInteger(quantidade) || quantidade < 0 || !Number.isFinite(preco) || preco < 0) {
      Alert.alert('Valores inválidos', 'Quantidade e preço devem ser números não negativos.');
      return;
    }
    try {
      await request('/api/itens', {
        method: 'POST',
        body: {
          ...cadastro,
          nome: cadastro.nome.trim(),
          descricao: cadastro.descricao.trim(),
          qtd: quantidade,
          preco,
          imagem: cadastro.imagem.trim(),
        },
      });
      await loadItems();
      setCadastro({ nome: '', descricao: '', qtd: '', preco: '', imagem: '' });
      setNotice('Cadastro concluído.');
      setScreen('estoque');
    } catch (error) {
      Alert.alert('Falha ao cadastrar item', error.message);
    }
  };

  const handleMovimentacao = async () => {
    const quantidade = Number(movimentacao.quantidade);
    if (!movimentacao.itemId) {
      Alert.alert('Item obrigatório', 'Selecione um item do estoque.');
      return;
    }
    if (!Number.isInteger(quantidade) || quantidade <= 0) {
      Alert.alert('Quantidade inválida', 'Informe uma quantidade inteira maior que zero.');
      return;
    }
    try {
      await request('/api/movimentacoes', {
        method: 'POST',
        body: {
          item_id: movimentacao.itemId,
          tipo: movimentacao.tipo,
          quantidade,
        },
      });
      await loadItems();
      setMovimentacao({ itemId: null, tipo: 'entrada', quantidade: '1' });
      setNotice('Movimentação concluída.');
      setScreen('estoque');
    } catch (error) {
      Alert.alert('Falha na movimentação', error.message);
    }
  };

  const handleCriarUsuario = async () => {
    if (!novoUsuario.nome.trim() || !novoUsuario.senha) {
      Alert.alert('Dados incompletos', 'Informe o nome e a senha do usuário.');
      return;
    }
    try {
      await request('/api/usuarios', {
        method: 'POST',
        body: { ...novoUsuario, nome: novoUsuario.nome.trim() },
      });
      await loadUsers();
      setNovoUsuario({ tipo: 'user', nome: '', senha: '' });
      setNotice('Usuário adicionado.');
    } catch (error) {
      Alert.alert('Falha ao criar usuário', error.message);
    }
  };

  const handleExportar = async () => {
    try {
      setCsvOutput(await request('/api/estoque/exportar-csv'));
      setNotice('CSV exportado.');
    } catch (error) {
      Alert.alert('Falha ao exportar CSV', error.message);
    }
  };

  const handleImportar = async () => {
    if (!csvInput.trim()) {
      Alert.alert('CSV vazio', 'Cole o conteúdo do arquivo CSV no campo.');
      return;
    }
    try {
      const result = await request('/api/estoque/importar-csv', {
        method: 'POST',
        body: { csv: csvInput },
      });
      await loadItems();
      setCsvInput('');
      setNotice(`${result.importados} item(ns) importado(s).`);
    } catch (error) {
      Alert.alert('Falha ao importar CSV', error.message);
    }
  };

  const handleExcluirTodos = () => {
    Alert.alert('Excluir todos os itens?', 'Esta ação remove todo o estoque do banco de dados.', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Excluir',
        style: 'destructive',
        onPress: async () => {
          try {
            await request('/api/itens', { method: 'DELETE' });
            setItems([]);
            setNotice('Estoque excluído.');
          } catch (error) {
            Alert.alert('Falha ao excluir estoque', error.message);
          }
        },
      },
    ]);
  };

  const navItems = useMemo(() => {
    const links = [
      { key: 'home', label: '?' },
      { key: 'movimentacao', label: 'MOVIMENTAÇÃO' },
      { key: 'cadastro', label: 'CADASTRO' },
      { key: 'estoque', label: 'ESTOQUE' },
      { key: 'logout', label: 'FECHAR' },
    ];
    if (currentUser?.tipo === 'admin') links.push({ key: 'adm', label: 'ADM' });
    return links;
  }, [currentUser]);

  const imageUri = (image) => {
    if (!image || !image.trim()) return null;
    const savedImage = image.trim().replace(/\\/g, '/');
    const apiUrl = apiBaseUrl().replace(/\/+$/, '');
    let path = savedImage;

    if (/^data:image\//i.test(savedImage)) return savedImage;

    if (/^https?:\/\//i.test(savedImage)) {
      const localUrl = savedImage.match(
        /^https?:\/\/(?:localhost|127(?:\.\d{1,3}){3}|\[::1\])(?::\d+)?(\/[^?#]*)?/i,
      );
      if (!localUrl) return savedImage;
      path = localUrl[1] || '';
    }

    path = path.replace(/^\/+/, '');
    path = path.replace(/^static\/(?!imagens\/)/i, 'static/imagens/');
    path = path.replace(/^imagens\//i, 'static/imagens/');
    if (!path.startsWith('static/')) path = `static/imagens/${path}`;

    const encodedPath = path
      .split('/')
      .map((segment) => {
        try {
          return encodeURIComponent(decodeURIComponent(segment));
        } catch (error) {
          return encodeURIComponent(segment);
        }
      })
      .join('/');
    return `${apiUrl}/${encodedPath}`;
  };

  const updateCadastro = (key, value) =>
    setCadastro((state) => ({ ...state, [key]: value }));
  const updateAdmin = (key, value) =>
    setNovoUsuario((state) => ({ ...state, [key]: value }));

  const renderField = (label, value, onChangeText, options = {}) => {
    const { loginField, multiline, ...inputOptions } = options;
    return (
      <View style={[styles.formField, loginField && styles.loginField]}>
        <Text style={[styles.fieldLabel, loginField && styles.loginFieldLabel]}>{label}</Text>
        <TextInput
          {...inputOptions}
          value={value}
          onChangeText={onChangeText}
          style={[
            styles.input,
            multiline && styles.multilineInput,
            loginField && styles.loginInput,
          ]}
          placeholderTextColor={loginField ? '#7582A8' : '#777'}
        />
      </View>
    );
  };

  const renderBrandHeader = () => (
    <View style={styles.siteHeader}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.navbar}
      >
        {navItems.map((item) => (
          <TouchableOpacity
            key={item.key}
            style={[styles.navButton, screen === item.key && styles.navButtonActive]}
            onPress={() => {
              setNotice('');
              if (item.key === 'logout') {
                handleLogout();
                return;
              }
              if (item.key === 'estoque') {
                loadItems().catch((error) => Alert.alert('Falha ao atualizar', error.message));
              }
              if (item.key === 'adm') {
                loadUsers().catch((error) => Alert.alert('Falha ao atualizar usuários', error.message));
              }
              setScreen(item.key);
            }}
          >
            <Text style={[styles.navButtonText, screen === item.key && styles.navButtonTextActive]}>
              {item.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      <Image
        source={require('./assets/senailogo.png')}
        style={styles.brandLogo}
        resizeMode="contain"
      />
    </View>
  );

  const renderHome = () => (
    <View style={styles.homeContent}>
      <Image source={require('./assets/roger-sem-fundo.png')} style={styles.homeImage} resizeMode="contain" />
    </View>
  );

  const renderStock = () => (
    <>
      <Text style={styles.pageTitle}>ALMOXARIFADO</Text>
      <ScrollView horizontal style={styles.tableScroll} contentContainerStyle={styles.tableScrollContent}>
        <View style={styles.tableContainer}>
          <View style={styles.tableHeaderRow}>
            {[
              ['Código:', 70],
              ['Nome:', 120],
              ['Descrição:', 170],
              ['Quantidade:', 110],
              ['Preço:', 100],
              ['Imagem:', 120],
            ].map(([label, width]) => (
              <Text key={label} style={[styles.tableHeaderCell, { width }]}>{label}</Text>
            ))}
          </View>
          {items.map((item) => (
            <View key={item.id} style={styles.tableRow}>
              <Text style={[styles.tableCell, { width: 70 }]}>{item.id}</Text>
              <Text style={[styles.tableCell, { width: 120 }]}>{item.nome}</Text>
              <Text style={[styles.tableCell, { width: 170 }]}>{item.descricao}</Text>
              <Text style={[styles.tableCell, { width: 110 }]}>{item.qtd}</Text>
              <Text style={[styles.tableCell, { width: 100 }]}>
                {Number(item.preco).toFixed(2).replace('.', ',')}
              </Text>
              <View style={[styles.tableCell, styles.imageCell, { width: 120 }]}>
                <TouchableOpacity
                  style={styles.tableButton}
                  onPress={() => {
                    const uri = imageUri(item.imagem);
                    if (uri) {
                      setPreviewImageError(false);
                      setPreviewImage(uri);
                    }
                  }}
                >
                  <Text style={styles.tableButtonText}>Ver Imagem</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>
      <View style={styles.stockActions}>
        <View style={styles.stockButtonRow}>
          <Button label="Exportar CSV" secondary onPress={handleExportar} />
        </View>
        {csvOutput ? (
          <TextInput
            value={csvOutput}
            editable={false}
            multiline
            selectTextOnFocus
            style={styles.csvOutput}
          />
        ) : null}
        <View style={styles.csvImport}>
          {renderField('Conteúdo CSV:', csvInput, setCsvInput, {
            placeholder: 'id;nome;descricao;qtd;preco;imagem',
            multiline: true,
          })}
          <Button label="Importar CSV" onPress={handleImportar} />
        </View>
      </View>
      {currentUser.tipo === 'admin' ? (
        <View style={styles.stockButtonRow}>
          <TouchableOpacity style={styles.standardButton} onPress={handleExcluirTodos}>
            <Text style={styles.standardButtonText}>Excluir todos os itens</Text>
          </TouchableOpacity>
        </View>
      ) : null}
    </>
  );

  const renderCadastro = () => (
    <>
      <Text style={styles.pageTitle}>CADASTRAR NOVOS ITENS</Text>
      <View style={styles.formContainer}>
        {renderField('Nome do Item:', cadastro.nome, (value) => updateCadastro('nome', value), {
          placeholder: 'Nome',
        })}
        {renderField('Descrição:', cadastro.descricao, (value) => updateCadastro('descricao', value), {
          placeholder: 'Descrição',
        })}
        {renderField('Quantidade:', cadastro.qtd, (value) => updateCadastro('qtd', value), {
          placeholder: 'Quantidade',
          keyboardType: 'numeric',
        })}
        {renderField('Preço:', cadastro.preco, (value) => updateCadastro('preco', value), {
          placeholder: 'Preço',
          keyboardType: 'decimal-pad',
        })}
        {renderField('Link para Imagem:', cadastro.imagem, (value) => updateCadastro('imagem', value), {
          placeholder: 'Link para Imagem',
          autoCapitalize: 'none',
        })}
        <Button label="Cadastrar" onPress={handleCadastro} />
      </View>
    </>
  );

  const renderMovimentacao = () => (
    <>
      <Text style={styles.pageTitle}>ADICIONAR E RETIRAR ITENS</Text>
      <View style={styles.formContainer}>
        <View style={styles.formField}>
          <Text style={styles.fieldLabel}>Tipo:</Text>
          <View style={styles.optionRow}>
            {[
              ['entrada', 'Entrada'],
              ['saida', 'Saída'],
            ].map(([tipo, label]) => (
              <TouchableOpacity
                key={tipo}
                style={[styles.standardButton, movimentacao.tipo === tipo && styles.optionSelected]}
                onPress={() => setMovimentacao((state) => ({ ...state, tipo }))}
              >
                <Text style={styles.standardButtonText}>{label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        <View style={styles.formField}>
          <Text style={styles.fieldLabel}>Nome do Item:</Text>
          <View style={styles.itemSelection}>
            {items.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={[
                  styles.itemOption,
                  movimentacao.itemId === item.id && styles.itemOptionSelected,
                ]}
                onPress={() => setMovimentacao((state) => ({ ...state, itemId: item.id }))}
              >
                <Text style={styles.itemOptionText}>{item.nome}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        {renderField('Quantidade:', movimentacao.quantidade, (value) =>
          setMovimentacao((state) => ({ ...state, quantidade: value })), {
          placeholder: 'Quantidade',
          keyboardType: 'numeric',
        })}
        <Button label="Movimentar" onPress={handleMovimentacao} />
      </View>
    </>
  );

  const renderAdm = () => (
    <>
      <Text style={styles.pageTitle}>CRIAR USUÁRIOS</Text>
      <View style={styles.formContainer}>
        <View style={styles.formField}>
          <Text style={styles.fieldLabel}>Tipo:</Text>
          <View style={styles.optionRow}>
            {[
              ['admin', 'Administrador'],
              ['user', 'Usuário'],
            ].map(([tipo, label]) => (
              <TouchableOpacity
                key={tipo}
                style={[styles.standardButton, novoUsuario.tipo === tipo && styles.optionSelected]}
                onPress={() => updateAdmin('tipo', tipo)}
              >
                <Text style={styles.standardButtonText}>{label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        {renderField('Nome do Usuário:', novoUsuario.nome, (value) => updateAdmin('nome', value), {
          placeholder: 'Nome',
        })}
        {renderField('Senha:', novoUsuario.senha, (value) => updateAdmin('senha', value), {
          placeholder: 'Senha',
          secureTextEntry: true,
        })}
        <Button label="Adicionar" onPress={handleCriarUsuario} />
      </View>
      <Text style={styles.userTableTitle}>USUÁRIOS CADASTRADOS</Text>
      <View style={styles.userTable}>
        <View style={styles.tableHeaderRow}>
          {[['ID', 80], ['Nome', 170], ['Tipo', 130]].map(([label, width]) => (
            <Text key={label} style={[styles.tableHeaderCell, { width }]}>{label}</Text>
          ))}
        </View>
        {users.map((user) => (
          <View key={user.id} style={styles.tableRow}>
            <Text style={[styles.tableCell, { width: 80 }]}>{user.id}</Text>
            <Text style={[styles.tableCell, { width: 170 }]}>{user.nome}</Text>
            <Text style={[styles.tableCell, { width: 130 }]}>{user.tipo}</Text>
          </View>
        ))}
      </View>
    </>
  );

  if (!currentUser) {
    return (
      <SafeAreaView style={styles.loginApp}>
        <StatusBar barStyle="light-content" backgroundColor={NAVY} />
        <ScrollView contentContainerStyle={styles.loginScroll} keyboardShouldPersistTaps="handled">
          <ImageBackground
            source={require('./assets/rogerio.png')}
            style={styles.loginHero}
            imageStyle={styles.loginHeroImage}
          >
            <View style={styles.loginTitleWrap}>
              <Text style={styles.loginTitle}>SISTEMA{'\n'}DE{'\n'}ALMOXARIFADO</Text>
            </View>
          </ImageBackground>
          <View style={styles.loginPanel}>
            {renderField('Usuário:', login.nome, (value) => setLogin((state) => ({ ...state, nome: value })), {
              placeholder: 'Nome',
              autoCapitalize: 'none',
              loginField: true,
            })}
            {renderField('Senha:', login.senha, (value) => setLogin((state) => ({ ...state, senha: value })), {
              placeholder: 'Senha',
              secureTextEntry: true,
              loginField: true,
            })}
            {loginError ? <Text style={styles.errorText}>{loginError}</Text> : null}
            <Button label="ENTRAR" onPress={handleLogin} login />
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.app}>
      <StatusBar barStyle="light-content" backgroundColor={NAVY} />
      {renderBrandHeader()}
      {notice ? (
        <TouchableOpacity onPress={() => setNotice('')} style={styles.notice}>
          <Text style={styles.noticeText}>{notice}</Text>
        </TouchableOpacity>
      ) : null}
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentInner}
        keyboardShouldPersistTaps="handled"
      >
        {screen === 'home' && renderHome()}
        {screen === 'estoque' && renderStock()}
        {screen === 'cadastro' && renderCadastro()}
        {screen === 'movimentacao' && renderMovimentacao()}
        {screen === 'adm' && currentUser.tipo === 'admin' && renderAdm()}
      </ScrollView>
      <Modal
        visible={Boolean(previewImage)}
        transparent
        animationType="fade"
        onRequestClose={() => setPreviewImage(null)}
      >
        <View style={styles.imageModalOverlay}>
          <View style={styles.imageModal}>
            {previewImage ? (
              <Image
                source={{ uri: previewImage }}
                style={styles.previewImage}
                resizeMode="contain"
                onError={() => setPreviewImageError(true)}
              />
            ) : null}
            {previewImageError ? (
              <Text style={styles.previewImageError}>
                Não foi possível carregar a imagem. Confira o link cadastrado.
              </Text>
            ) : null}
            <TouchableOpacity style={styles.imageModalClose} onPress={() => setPreviewImage(null)}>
              <Text style={styles.imageModalCloseText}>Fechar</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function Button({ label, onPress, secondary = false, login = false }) {
  return (
    <TouchableOpacity
      style={[
        styles.primaryButton,
        secondary && styles.secondaryButton,
        login && styles.loginButton,
      ]}
      onPress={onPress}
      activeOpacity={0.82}
    >
      <Text style={[styles.primaryButtonText, secondary && styles.secondaryButtonText]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  app: { flex: 1, backgroundColor: NAVY, fontFamily: 'Arial' },
  loginApp: { flex: 1, backgroundColor: NAVY },
  loginScroll: { flexGrow: 1, backgroundColor: NAVY },
  loginHero: { height: 330, justifyContent: 'flex-end', backgroundColor: NAVY },
  loginHeroImage: { resizeMode: 'cover' },
  loginTitleWrap: {
    alignSelf: 'flex-end',
    width: '54%',
    paddingHorizontal: 12,
    paddingBottom: 24,
    backgroundColor: 'rgba(25,42,107,0.28)',
  },
  loginTitle: { color: '#FFFFFF', fontSize: 23, lineHeight: 27, fontWeight: 'bold' },
  loginPanel: { width: '56%', alignSelf: 'flex-end', paddingHorizontal: 16, paddingTop: 11 },
  loginField: { backgroundColor: 'transparent', padding: 0, borderWidth: 0, marginBottom: 12 },
  loginFieldLabel: { color: GOLD, borderRightWidth: 0, padding: 0, marginBottom: 5 },
  loginInput: { minHeight: 42, borderRadius: 18, backgroundColor: '#FFFFFF', paddingHorizontal: 12 },
  errorText: { color: '#FFFFFF', fontSize: 13, marginBottom: 8 },
  siteHeader: { height: 75, backgroundColor: NAVY, position: 'relative', zIndex: 1 },
  navbar: {
    minWidth: '100%',
    height: 75,
    paddingHorizontal: 6,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
  },
  navButton: { minHeight: 45, paddingVertical: 12, paddingHorizontal: 8, marginHorizontal: 1, justifyContent: 'center' },
  navButtonActive: { borderRadius: 24, backgroundColor: '#F3F4F8' },
  navButtonText: { color: NAVY, fontSize: 10, fontWeight: 'bold', textAlign: 'center' },
  navButtonTextActive: { textDecorationLine: 'underline' },
  brandLogo: { position: 'absolute', top: 82, left: 10, width: '20%', height: 50, zIndex: 2 },
  notice: { paddingHorizontal: 10, paddingVertical: 6, backgroundColor: NAVY },
  noticeText: { color: '#FFFFFF', fontSize: 13, textAlign: 'center' },
  content: { flex: 1, backgroundColor: NAVY },
  contentInner: { paddingHorizontal: 10, paddingTop: 35, paddingBottom: 22 },
  pageTitle: {
    color: '#FFFFFF',
    textAlign: 'center',
    fontFamily: 'Arial',
    fontSize: 27,
    fontWeight: 'bold',
    letterSpacing: 1,
    marginTop: 6,
    marginBottom: 20,
  },
  homeContent: { flex: 1, minHeight: 500, alignItems: 'center', marginTop: 15 },
  homeImage: { width: 400, maxWidth: '100%', height: 420 },
  formContainer: { width: '100%', maxWidth: 650, alignSelf: 'center', marginBottom: 30 },
  formField: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 10,
    marginBottom: 10,
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.08)',
  },
  fieldLabel: {
    flexShrink: 0,
    minWidth: 95,
    maxWidth: '40%',
    color: NAVY,
    fontSize: 13,
    fontWeight: 'bold',
    paddingRight: 9,
    borderRightWidth: 1,
    borderRightColor: 'rgba(25,42,107,0.2)',
  },
  input: {
    flex: 1,
    minWidth: 0,
    minHeight: 42,
    paddingHorizontal: 10,
    paddingVertical: 9,
    backgroundColor: '#FFFFFF',
    borderWidth: 0,
    color: NAVY,
    fontFamily: 'Arial',
    fontSize: 14,
  },
  multilineInput: { height: 90, textAlignVertical: 'top' },
  primaryButton: {
    alignSelf: 'center',
    backgroundColor: GOLD,
    borderWidth: 2,
    borderColor: NAVY,
    borderRadius: 10,
    paddingHorizontal: 20,
    paddingVertical: 11,
    marginTop: 8,
  },
  primaryButtonText: { color: NAVY, fontSize: 16, fontWeight: 'bold', textAlign: 'center' },
  secondaryButton: { backgroundColor: '#FFFFFF', borderColor: '#FFFFFF' },
  secondaryButtonText: { color: NAVY, fontSize: 13, fontWeight: 'normal' },
  loginButton: { backgroundColor: '#CA7B16', borderColor: '#CA7B16', alignSelf: 'flex-start' },
  stockTitleBlock: { marginBottom: 20 },
  tableScroll: { maxHeight: 480, width: '100%' },
  tableScrollContent: { paddingBottom: 4 },
  tableContainer: { minWidth: 690, backgroundColor: '#FFFFFF' },
  tableHeaderRow: { flexDirection: 'row', backgroundColor: TABLE_NAVY },
  tableHeaderCell: {
    minHeight: 40,
    paddingHorizontal: 5,
    paddingVertical: 9,
    color: '#FFFFFF',
    backgroundColor: TABLE_NAVY,
    textAlign: 'center',
    fontFamily: 'Arial',
    fontSize: 13,
    fontWeight: 'bold',
  },
  tableRow: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#DDDDDD',
  },
  tableCell: {
    minHeight: 42,
    paddingHorizontal: 5,
    paddingVertical: 9,
    color: NAVY,
    textAlign: 'center',
    textAlignVertical: 'center',
    fontFamily: 'Arial',
    fontSize: 13,
    borderBottomWidth: 1,
    borderBottomColor: '#DDDDDD',
  },
  imageCell: { justifyContent: 'center', alignItems: 'center' },
  tableButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 7,
  },
  tableButtonText: { color: NAVY, fontSize: 12, textAlign: 'center' },
  stockActions: { width: '95%', alignSelf: 'center', marginTop: 8, marginBottom: 22 },
  stockButtonRow: { flexDirection: 'row', justifyContent: 'flex-end', marginBottom: 5 },
  standardButton: {
    backgroundColor: '#FFFFFF',
    borderColor: '#FFFFFF',
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 9,
    marginHorizontal: 3,
    marginVertical: 3,
    alignItems: 'center',
    justifyContent: 'center',
  },
  standardButtonText: { color: NAVY, fontSize: 13, textAlign: 'center' },
  csvImport: { marginTop: 6 },
  csvOutput: {
    minHeight: 95,
    maxHeight: 180,
    marginVertical: 8,
    backgroundColor: '#FFFFFF',
    padding: 9,
    color: NAVY,
    fontSize: 11,
  },
  optionRow: { flex: 1, flexDirection: 'row', flexWrap: 'wrap' },
  optionSelected: { backgroundColor: GOLD, borderColor: NAVY },
  itemSelection: { flex: 1, flexDirection: 'row', flexWrap: 'wrap' },
  itemOption: { borderWidth: 1, borderColor: '#D5D5D5', borderRadius: 8, padding: 8, margin: 3 },
  itemOptionSelected: { backgroundColor: GOLD, borderColor: NAVY },
  itemOptionText: { color: NAVY, fontSize: 12 },
  userTableTitle: {
    color: '#FFFFFF',
    textAlign: 'center',
    fontFamily: 'Arial',
    fontSize: 22,
    fontWeight: 'bold',
    marginTop: 24,
    marginBottom: 12,
  },
  userTable: { alignSelf: 'center', backgroundColor: '#FFFFFF', marginBottom: 24 },
  imageModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  imageModal: { width: '100%', maxWidth: 480, backgroundColor: '#FFFFFF', padding: 14, borderRadius: 8 },
  previewImage: { width: '100%', height: 250 },
  previewImageError: { color: '#B42318', fontSize: 14, textAlign: 'center', marginTop: 8 },
  imageModalClose: { alignSelf: 'center', backgroundColor: GOLD, borderRadius: 8, padding: 10, marginTop: 12 },
  imageModalCloseText: { color: NAVY, fontWeight: 'bold' },
});
