#!/usr/bin/env python3
"""
MCP Ecosystem Platform Startup Script - DEPRECATED

⚠️  Bu script artık kullanılmıyor!
🎯 Faz 0: Stabilizasyon - Tek Noktadan Kontrol

Lütfen bunun yerine kullanın:
    python start-dev.py

Bu script tüm sistemi (Backend + Frontend + MCP Manager) tek komutla başlatır.
"""

import sys
import subprocess

def main():
    """Redirect to the new unified startup script"""
    print("🚨 DEPRECATED: start.py artık kullanılmıyor!")
    print("=" * 50)
    print("🎯 Faz 0: Stabilizasyon - Tek Noktadan Kontrol")
    print("")
    print("✅ Lütfen bunun yerine kullanın:")
    print("   python start-dev.py")
    print("")
    print("🔄 Otomatik olarak yeni script'e yönlendiriliyor...")
    print("=" * 50)
    
    # Automatically run the new script
    try:
        subprocess.run([sys.executable, "start-dev.py"])
    except KeyboardInterrupt:
        print("\n🛑 İşlem iptal edildi")
    except Exception as e:
        print(f"❌ Hata: {e}")
        print("Manuel olarak çalıştırın: python start-dev.py")

if __name__ == "__main__":
    main()
