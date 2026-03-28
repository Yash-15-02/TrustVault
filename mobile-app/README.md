# TrustVault (React Native)

Use the same JSON API as the web demo:

- `POST /analyze` on your backend (e.g. `http://<LAN-IP>:5000/analyze` from a device)
- `GET /health`

Example body:

```json
{
  "amount": 50000,
  "is_new_receiver": 1,
  "transactions_today": 1,
  "message": "Your OTP is 123456"
}
```

When `alert` is non-null or `delay_transaction` is true, show a full-screen warning and optional countdown before allowing "proceed anyway".

Create the app with `npx create-expo-app` or `npx @react-native-community/cli init`, add `axios` or `fetch`, and point `baseURL` at your machine's IP (not `localhost` on physical devices).
