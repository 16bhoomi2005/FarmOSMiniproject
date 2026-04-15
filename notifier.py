import os
import streamlit as st
from datetime import datetime

def get_twilio_client():
    try:
        from twilio.rest import Client
    except ImportError:
        return None
        
    try:
        sid = st.secrets.get("TWILIO_SID") or os.environ.get("TWILIO_SID")
        token = st.secrets.get("TWILIO_TOKEN") or os.environ.get("TWILIO_TOKEN")
        if not sid or not token:
            return None
        return Client(sid, token)
    except Exception:
        return None

def send_sms_alert(alert: dict, to_number: str) -> dict:
    """
    alert dict keys:
      field, severity, type, message, value, unit, timestamp
    Returns: 
      {success: bool, sid: str, error: str}
    """
    # ── COOLDOWN CHECK ──
    cooldown_key = f"sms_{alert.get('field')}_{alert.get('type')}"
    last_sent = st.session_state.get('sms_cooldowns', {}).get(cooldown_key)
    from datetime import datetime, timedelta
    
    if last_sent and (datetime.now() - last_sent) < timedelta(hours=1):
        # Already sent recently, skip to avoid spam
        return {"success": False, "error": "Cooldown active", "simulated": True}

    client = get_twilio_client()
    try:
        from_number = st.secrets.get("TWILIO_FROM") or os.environ.get("TWILIO_FROM")
    except Exception:
        from_number = None
    
    if not client or not from_number:
        return {
            "success": False, 
            "error": "Twilio not configured",
            "simulated": True
        }
    
    emoji = {"Critical": "🚨 URGENT", "Warning": "⚠️ WARN", "Info": "ℹ️ INFO"}
    
    body = (
        f"FarmOS {emoji.get(alert.get('severity', ''), '')} ALERT\n"
        f"📍 Field: {alert.get('field', 'Global')}\n"
        f"🔸 Issue: {alert.get('type', 'Condition')}\n"
        f"📉 Value: {alert.get('value', '')} {alert.get('unit', '')}\n"
        f"✅ Action: {alert.get('message', '')}\n"
    )
    
    try:
        print(f"DEBUG: Attempting to send SMS to {to_number} via Twilio...")
        msg = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        # Update cooldown
        if 'sms_cooldowns' not in st.session_state:
            st.session_state.sms_cooldowns = {}
        st.session_state.sms_cooldowns[cooldown_key] = datetime.now()
        
        print(f"DEBUG: SMS sent successfully. Message SID: {msg.sid}")
        return {"success": True, "sid": msg.sid}
    except Exception as e:
        print(f"DEBUG: SMS failed to send. Error: {str(e)}")
        return {"success": False, "error": str(e), "simulated": False}

def notify_batch(alerts: list, to_number: str) -> list:
    """Send only Critical severity alerts."""
    critical = [a for a in alerts if a.get("severity") == "Critical"]
    results = []
    # Send max 2 per batch to minimize Twilio costs/spam
    for alert in critical[:2]:
        result = send_sms_alert(alert, to_number)
        results.append({**alert, **result})
    return results
