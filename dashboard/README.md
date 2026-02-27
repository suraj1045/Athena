# Athena Dashboard — Frontend Applications

This directory contains the frontend applications for Athena:

## `/officer-app`
React Native mobile application for field officers.
- Receives real-time intercept alerts via AppSync GraphQL subscriptions
- Displays officer location on a live map
- Shows vehicle details, violation type, and navigation to intercept point
- Maintains shift-based alert history

## `/control-dashboard`
React web dashboard for the central Dispatch / Command Center.
- Real-time city-wide incident map
- Critical vehicle tracking overlay
- Camera health monitoring grid
- System performance metrics and analytics

## Tech Stack
- **Officer App:** React Native + Expo + AWS AppSync
- **Control Dashboard:** React 18 + Vite + Mapbox GL + AppSync
- **State Management:** Zustand
- **Maps:** Mapbox GL JS / React Native Maps
