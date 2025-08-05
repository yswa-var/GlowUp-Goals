import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View, Text, Button } from 'react-native';
import AppleAuthButton from './components/AppleAuthButton';
import { useAuth } from './hooks/useAuth';

export default function App() {
  const { user, loading, signOut } = useAuth();

  if (loading) {
    return (
      <View style={styles.container}>
        <Text>Loading...</Text>
      </View>
    );
  }

  if (user) {
    return (
      <View style={styles.container}>
        <Text style={styles.welcomeTitle}>Welcome! stranger</Text>
        <Text style={styles.welcomeSubtitle}>No guilt, no judgment - just tiny steps that actually work.</Text>
        <Button title="Sign Out" onPress={signOut} />
        <StatusBar style="auto" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <AppleAuthButton />
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  welcomeTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 16,
    color: '#333',
  },
  welcomeSubtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 32,
    color: '#666',
    paddingHorizontal: 32,
    lineHeight: 24,
  },
});
