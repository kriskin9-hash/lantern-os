#!/usr/bin/env python3
"""
Lantern OS MCP Server Public Tunnel
Creates a public URL for accessing the Lantern OS MCP server via pyngrok
"""

import os
import sys
from pyngrok import ngrok

def main():
    # Kill any stuck endpoints
    print("🧹 Cleaning up old ngrok sessions...")
    os.system("taskkill /F /IM ngrok.exe 2>/dev/null || true")

    import time
    time.sleep(2)

    # Set ngrok authtoken
    authtoken = "3CvizblAm2dzsHxdcsOYqPfoZO2_2K26cM1f1XAjPYFbGdcUZ"
    ngrok.set_auth_token(authtoken)

    # Disconnect any existing tunnels
    try:
        for tunnel in ngrok.get_tunnels():
            print(f"Disconnecting {tunnel.public_url}")
            ngrok.disconnect(tunnel.public_url)
    except Exception as e:
        print(f"Note: {e}")

    time.sleep(2)

    # Create tunnel to MCP server
    print("\n🚀 Creating tunnel to Lantern OS MCP Server (port 8771)...")
    try:
        # Use pyngrok which handles the ngrok session differently
        public_url = ngrok.connect(8771, "http")
        print(f"\n✅ SUCCESS! MCP Server is now publicly accessible!")
        print(f"\n🌐 PUBLIC URL: {public_url}")
        print(f"\nShare this URL with external services to connect to Lantern OS MCP\n")

        # Keep the tunnel alive
        print("Tunnel is live. Press Ctrl+C to stop...\n")
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nFallback: MCP server is available locally at http://127.0.0.1:8771")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
