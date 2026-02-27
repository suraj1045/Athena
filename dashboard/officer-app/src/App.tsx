/**
 * Athena Officer App — Entry Point
 *
 * React Native mobile application for field officers.
 * Receives real-time intercept alerts and displays them on a map.
 */

import React from 'react';
import { SafeAreaView, StatusBar, StyleSheet, Text, View } from 'react-native';

const App: React.FC = () => {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0D1117" />
      <View style={styles.header}>
        <Text style={styles.title}>🏛️ ATHENA</Text>
        <Text style={styles.subtitle}>Officer Dashboard</Text>
      </View>
      <View style={styles.mapPlaceholder}>
        <Text style={styles.placeholderText}>
          Map View — Intercept Alerts will appear here
        </Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D1117',
  },
  header: {
    padding: 16,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#21262D',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#58A6FF',
  },
  subtitle: {
    fontSize: 14,
    color: '#8B949E',
    marginTop: 4,
  },
  mapPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#161B22',
    margin: 16,
    borderRadius: 12,
  },
  placeholderText: {
    color: '#8B949E',
    fontSize: 16,
  },
});

export default App;
