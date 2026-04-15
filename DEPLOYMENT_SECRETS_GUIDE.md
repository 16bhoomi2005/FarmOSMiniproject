# 🔑 FarmOS Deployment Secrets Guide

When you deploy to **Streamlit Community Cloud** or **Railway**, you must manually add your secrets in their dashboard. **Do NOT upload your `.env` file to GitHub.**

### 📋 Secrets to Add
Copy these exact keys and values from your local `.env` file:

| Key | Description |
| :--- | :--- |
| `MONGO_URI` | Your MongoDB Atlas connection string. |
| `TWILIO_ACCOUNT_SID` | Found in your Twilio Console. |
| `TWILIO_AUTH_TOKEN` | Found in your Twilio Console. |
| `TWILIO_PHONE_NUMBER` | Your Twilio virtual phone number. |
| `USER_PHONE_NUMBER` | Your personal phone number for alerts. |
| `GOOGLE_API_KEY` | Your Gemini AI API Key. |
| `GEE_SERVICE_ACCOUNT` | Your Google Earth Engine service account email. |

### 🛠️ How to Add on Streamlit Community Cloud
1.  Go to your app on the [Streamlit Dashboard](https://share.streamlit.io/).
2.  Click **Settings** -> **Secrets**.
3.  Paste the values in the following TOML format:
    ```toml
    MONGO_URI = "your_connection_string"
    TWILIO_ACCOUNT_SID = "your_sid"
    # ... and so on
    ```

### 🛰️ Google Earth Engine Note
If you use Earth Engine, you will need to download your `private_key.json` and optionally handle it as a secret string, or ensure your `GEE_SERVICE_ACCOUNT` has appropriate permissions for the cloud environment.

> [!IMPORTANT]
> If your app fails with a `ModuleNotFoundError` after deploying, check that `requirements.txt` is in the root directory and contains all necessary packages.
