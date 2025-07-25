# 🔧 Kiro IDE Extension Connection Debug

## Problem Analizi
Extension "Connection Error" gösteriyor ama backend API çalışıyor.

## Çözüm Adımları

### 1. Kiro IDE Extension Konfigürasyonu
1. **Kiro IDE'yi aç**
2. **File → Preferences → Settings**
3. **"MCP Platform" ara**
4. **Şu ayarları yap:**
   - `mcpPlatform.apiUrl`: `http://localhost:8001`
   - `mcpPlatform.apiKey`: (boş bırak)
   - `mcpPlatform.notificationLevel`: `all`

### 2. Extension Test
1. **test-file.js dosyasını aç**
2. **Sağ tık → "Review Current File"**
3. **VEYA Command Palette:** `Ctrl+Shift+P` → "Review Current File"

### 3. Developer Console Debug
1. **Help → Toggle Developer Tools**
2. **Console tab'ına git**
3. **Bu mesajları ara:**
   ```
   🔧 MCPPlatformAPI initialized with URL: http://localhost:8001
   🌐 Creating API client with baseURL: http://localhost:8001/api/v1
   📤 Making POST request to /git/review
   ```

### 4. Network Analysis MCP Server Sorunu
Backend loglarında `network-analysis` MCP server başlatılamıyor. Bu sorunu çözmek için:

1. **MCP konfigürasyonunu kontrol et:**
   - `.kiro/settings/mcp.json` dosyasında `network-analysis` server'ı var
   - Python path'i doğru: `C:\Users\TT\CLONE\Kairos_The_Context_Keeper\venv\Scripts\python.exe`
   - Script path'i doğru: `C:\Users\TT\CLONE\Kairos_The_Context_Keeper\network-analysis-mcp.py`

2. **Script'in var olup olmadığını kontrol et:**
   ```cmd
   dir "C:\Users\TT\CLONE\Kairos_The_Context_Keeper\network-analysis-mcp.py"
   ```

3. **Python environment'ı kontrol et:**
   ```cmd
   "C:\Users\TT\CLONE\Kairos_The_Context_Keeper\venv\Scripts\python.exe" --version
   ```

### 5. Alternatif Çözümler

#### A. Port Değiştir
Eğer 8001 portu sorun yaratıyorsa:
1. **Backend'i farklı portta başlat:**
   ```python
   # start-dev.py içinde port'u değiştir
   uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
   ```
2. **Extension ayarlarında URL'yi güncelle:**
   - `mcpPlatform.apiUrl`: `http://localhost:8003`

#### B. CORS Problemi
Backend'de CORS ayarlarını kontrol et:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme için
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### C. Extension Yeniden Yükle
1. **Kiro IDE'yi tamamen kapat**
2. **Yeniden başlat**
3. **Extension'ı devre dışı bırak ve tekrar etkinleştir**

### 6. Test Komutları

#### Backend API Test:
```bash
curl -X POST "http://localhost:8001/api/v1/git/review" \
  -H "Content-Type: application/json" \
  -d '{"repository_path": ".", "review_type": "full"}'
```

#### Extension Debug:
1. **Developer Console'da şu komutu çalıştır:**
   ```javascript
   fetch('http://localhost:8001/api/v1/mcp/status')
     .then(r => r.json())
     .then(console.log)
     .catch(console.error)
   ```

### 7. Beklenen Sonuçlar

#### ✅ Başarılı:
- Extension "Connection Error" göstermez
- Developer Console'da API çağrıları görünür
- Backend loglarında başarılı istekler görünür

#### ❌ Başarısız:
- "Connection Error" devam eder
- Console'da network hataları görünür
- Backend'e istek ulaşmaz

## Sonraki Adımlar
Bu adımları takip ettikten sonra sonuçları paylaş, gerekirse ek debug adımları ekleyeceğim.