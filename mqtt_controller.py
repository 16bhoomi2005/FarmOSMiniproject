import json, time
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    PAHO_AVAILABLE = False

BROKER = "broker.hivemq.com"
PORT   = 1883
BASE_TOPIC = "smartfarm/irrigation"

def publish_command(field: str, command: str, duration_min: int = 20, farm_id: str = "farm_001") -> dict:
    if not PAHO_AVAILABLE:
        return {"success": False, "error": "paho-mqtt library is missing. Run: pip install paho-mqtt"}

    """
    command: "ON" | "OFF" | "AUTO"
    Publishes to: smartfarm/irrigation/{farm_id}/{field}/cmd
    Returns: {success, topic, payload, timestamp, broker}
    """
    topic = f"{BASE_TOPIC}/{farm_id}/{field}/cmd"
    
    payload = {
        "command":  command,
        "field":    field,
        "duration": duration_min,
        "farm_id":  farm_id,
        "timestamp": datetime.utcnow().isoformat(),
        "source":   "SmartFarm_Dashboard"
    }
    
    result = {
        "success": False, 
        "topic": topic,
        "payload": payload,
        "broker": BROKER
    }
    
    def on_connect(client, userdata, flags, rc):
        userdata["connected"] = (rc == 0)
    
    client = mqtt.Client(client_id=f"smartfarm_{farm_id}_{field}_{int(time.time())}", userdata={"connected": False})
    client.on_connect = on_connect
    
    try:
        client.connect(BROKER, PORT, keepalive=10)
        client.loop_start()
        time.sleep(1.5)  # wait for connection
        
        if client._userdata["connected"]:
            info = client.publish(topic, json.dumps(payload), qos=1)
            info.wait_for_publish(timeout=3)
            result["success"] = True
            result["message_id"] = info.mid
        else:
            result["error"] = "Broker unreachable"
    except Exception as e:
        result["error"] = str(e)
    finally:
        client.loop_stop()
        client.disconnect()
    
    return result

def publish_bulk(fields: list, command: str, farm_id: str = "farm_001") -> list:
    return [publish_command(f, command, farm_id=farm_id) for f in fields]

def get_subscribe_code(farm_id: str = "farm_001") -> str:
    """Returns Arduino/ESP32 snippet for copy-paste into hardware code."""
    return f"""// Arduino/ESP32 MQTT Subscriber
// Paste into your sketch to receive commands from the SmartFarm Dashboard

#include <PubSubClient.h>
const char* mqtt_server = "{BROKER}";
const char* topic = "{BASE_TOPIC}/{farm_id}/+/cmd";

void callback(char* t, byte* p, unsigned int len) {{
  String msg = String((char*)p).substring(0, len);
  
  // Parse JSON and control relay/valve
  if (msg.indexOf("ON") > 0 || msg.indexOf("AUTO") > 0) {{
    digitalWrite(RELAY_PIN, HIGH);
  }} else if (msg.indexOf("OFF") > 0) {{
    digitalWrite(RELAY_PIN, LOW);
  }}
}}
"""
