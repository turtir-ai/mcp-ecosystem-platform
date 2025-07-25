# 🔧 Yaygın Sorunlar ve AI Çözümleri

Bu rehber, MCP Ecosystem Platform'da karşılaşabileceğiniz yaygın sorunları ve AI'ın önerdiği çözümleri içerir.

## 📋 İçindekiler

- [MCP Sunucu Sorunları](#mcp-sunucu-sorunları)
- [Sistem Performans Sorunları](#sistem-performans-sorunları)
- [Veritabanı Sorunları](#veritabanı-sorunları)
- [Ağ Bağlantı Sorunları](#ağ-bağlantı-sorunları)
- [AI Sistem Sorunları](#ai-sistem-sorunları)
- [Frontend Sorunları](#frontend-sorunları)
- [Güvenlik Sorunları](#güvenlik-sorunları)

## 🖥️ MCP Sunucu Sorunları

### ❌ Sorun: MCP Sunucu Offline

**Belirtiler:**
- Sunucu durumu "OFFLINE" olarak görünüyor
- API çağrıları başarısız oluyor
- Hata mesajı: "Connection refused"

**AI Analizi:**
```json
{
  "problem": "MCP server connection failure",
  "confidence": 0.9,
  "possible_causes": [
    "Server process crashed",
    "Port configuration changed",
    "Network connectivity issue",
    "Resource exhaustion"
  ]
}
```

**AI Önerilen Çözümler:**

#### 🔄 Çözüm 1: Sunucu Yeniden Başlatma (AI Önerisi)
```bash
# AI otomatik önerisi - Onay gerekli
curl -X POST "http://localhost:8001/api/v1/ai/mcp/restart/groq-llm" \
  -H "Content-Type: application/json" \
  -d '{"reasoning": "Server appears offline"}'
```

#### 🔍 Çözüm 2: Log Analizi
```bash
# AI log analizi
curl "http://localhost:8001/api/v1/ai/mcp/logs/groq-llm?lines=50"
```

#### ⚙️ Çözüm 3: Manuel Restart
```bash
# Manuel sunucu restart
docker restart mcp-groq-llm
# veya
systemctl restart mcp-groq-llm
```

**Önleme:**
- Proaktif izlemeyi etkinleştirin
- Resource limit'leri ayarlayın
- Health check interval'ını optimize edin

---

### ⚠️ Sorun: MCP Sunucu Degraded Performance

**Belirtiler:**
- Yavaş yanıt süreleri (>500ms)
- Intermittent connection errors
- Yüksek CPU/Memory kullanımı

**AI Analizi:**
```json
{
  "problem": "Performance degradation",
  "confidence": 0.85,
  "metrics": {
    "avg_response_time": 750,
    "error_rate": 0.15,
    "cpu_usage": 85
  }
}
```

**AI Önerilen Çözümler:**

#### 📊 Çözüm 1: Süreç Analizi (AI Otomatik)
```bash
# AI süreç araştırması
curl -X POST "http://localhost:8001/api/v1/ai/system/investigate-processes" \
  -d '{"reasoning": "High response time detected"}'
```

#### 🔧 Çözüm 2: Resource Optimization
```bash
# Container resource limit'lerini artır
docker update --memory=2g --cpus=1.5 mcp-groq-llm
```

#### 🔄 Çözüm 3: Graceful Restart
```bash
# Graceful restart with warm-up
curl -X POST "http://localhost:8001/api/v1/mcp/restart/groq-llm" \
  -H "X-Restart-Mode: graceful"
```

---

## 🚀 Sistem Performans Sorunları

### 🔥 Sorun: Yüksek CPU Kullanımı

**Belirtiler:**
- CPU kullanımı >85%
- Sistem yanıt süreleri yavaş
- Load average yüksek

**AI Analizi:**
```json
{
  "problem": "High CPU usage",
  "confidence": 0.95,
  "top_processes": [
    {"name": "python", "cpu": 25.5, "pid": 1234},
    {"name": "node", "cpu": 18.3, "pid": 5678}
  ],
  "recommendation": "investigate_processes"
}
```

**AI Önerilen Çözümler:**

#### 🔍 Çözüm 1: AI Süreç Analizi
```bash
# AI otomatik süreç analizi
curl -X POST "http://localhost:8001/api/v1/ai/system/investigate-processes"
```

#### ⚡ Çözüm 2: Resource-Intensive Process'leri Optimize Et
```bash
# CPU-intensive process'leri tespit et
ps aux --sort=-%cpu | head -10

# Process priority'sini düşür
renice +10 -p <PID>
```

#### 🔄 Çözüm 3: Service Restart (AI Önerisi)
```bash
# AI service restart önerisi
curl -X POST "http://localhost:8001/api/v1/ai/system/restart-services" \
  -d '{"services": ["high-cpu-service"], "reasoning": "CPU optimization"}'
```

---

### 💾 Sorun: Yüksek Memory Kullanımı

**Belirtiler:**
- Memory kullanımı >90%
- OOM (Out of Memory) errors
- Swap kullanımı yüksek

**AI Analizi:**
```json
{
  "problem": "Memory exhaustion",
  "confidence": 0.92,
  "memory_usage": 92.3,
  "swap_usage": 45.2,
  "recommendation": "restart_services"
}
```

**AI Önerilen Çözümler:**

#### 🧹 Çözüm 1: Memory Cleanup (AI Otomatik)
```bash
# AI memory cleanup
curl -X POST "http://localhost:8001/api/v1/ai/system/memory-cleanup"
```

#### 🔄 Çözüm 2: Service Restart
```bash
# Memory-intensive servisleri restart et
docker restart $(docker ps --filter "label=memory-intensive" -q)
```

#### 📊 Çözüm 3: Memory Monitoring
```bash
# Memory kullanımını izle
watch -n 1 'free -h && echo "---" && ps aux --sort=-%mem | head -10'
```

---

## 🗄️ Veritabanı Sorunları

### 🐌 Sorun: Yüksek Database Latency

**Belirtiler:**
- DB query süreleri >200ms
- Connection pool exhaustion
- Slow query warnings

**AI Analizi:**
```json
{
  "problem": "Database performance issue",
  "confidence": 0.88,
  "metrics": {
    "avg_latency": 350,
    "slow_queries": 15,
    "connection_pool_usage": 0.95
  },
  "recommendation": "optimize_queries"
}
```

**AI Önerilen Çözümler:**

#### 🔍 Çözüm 1: Query Analysis
```sql
-- Slow query'leri tespit et
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

#### ⚙️ Çözüm 2: Connection Pool Optimization
```python
# Connection pool ayarları
DATABASE_CONFIG = {
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 3600
}
```

#### 🔄 Çözüm 3: Database Maintenance
```bash
# AI database maintenance önerisi
curl -X POST "http://localhost:8001/api/v1/ai/database/maintenance" \
  -d '{"operations": ["vacuum", "reindex"], "reasoning": "High latency detected"}'
```

---

## 🌐 Ağ Bağlantı Sorunları

### 🔌 Sorun: API Connection Timeout

**Belirtiler:**
- "Connection timeout" errors
- Intermittent API failures
- Network latency spikes

**AI Analizi:**
```json
{
  "problem": "Network connectivity issue",
  "confidence": 0.75,
  "possible_causes": [
    "Network congestion",
    "DNS resolution issues",
    "Firewall blocking",
    "Service overload"
  ]
}
```

**AI Önerilen Çözümler:**

#### 🔍 Çözüm 1: Network Diagnostics
```bash
# AI network analizi
curl -X POST "http://localhost:8001/api/v1/monitoring/analyze-connection-loss" \
  -d '{"component": "API", "error_details": "Connection timeout"}'
```

#### 🌐 Çözüm 2: DNS ve Network Test
```bash
# DNS resolution test
nslookup api.example.com

# Network connectivity test
ping -c 4 api.example.com
traceroute api.example.com
```

#### ⚙️ Çözüm 3: Timeout Configuration
```javascript
// API client timeout ayarları
const apiClient = axios.create({
  timeout: 30000,
  retry: 3,
  retryDelay: 1000
});
```

---

## 🤖 AI Sistem Sorunları

### ❌ Sorun: AI Approval System Not Working

**Belirtiler:**
- Approval request'ler pending kalıyor
- AI actions execute edilmiyor
- Security manager errors

**AI Analizi:**
```json
{
  "problem": "AI approval workflow failure",
  "confidence": 0.9,
  "pending_approvals": 5,
  "last_approval": "2024-01-15T08:30:00Z"
}
```

**Çözümler:**

#### 🔍 Çözüm 1: Approval Status Check
```bash
# Pending approval'ları kontrol et
curl "http://localhost:8001/api/v1/security/approvals"
```

#### 🔄 Çözüm 2: Manual Approval
```bash
# Manuel approval
curl -X POST "http://localhost:8001/api/v1/security/approve/{operation_id}"
```

#### ⚙️ Çözüm 3: Security Manager Restart
```bash
# Security manager'ı restart et
docker restart mcp-security-manager
```

---

### 🚨 Sorun: Proactive Monitoring Not Detecting Issues

**Belirtiler:**
- Alerts oluşturulmuyor
- Pattern detection çalışmıyor
- Health history boş

**Çözümler:**

#### 🔄 Çözüm 1: Monitoring Restart
```bash
# Proactive monitoring'i restart et
curl -X POST "http://localhost:8001/api/v1/monitoring/stop"
curl -X POST "http://localhost:8001/api/v1/monitoring/start"
```

#### ⚙️ Çözüm 2: Configuration Check
```bash
# Monitoring config'ini kontrol et
curl "http://localhost:8001/api/v1/monitoring/config"
```

---

## 🖥️ Frontend Sorunları

### 🔄 Sorun: Real-time Updates Not Working

**Belirtiler:**
- System status güncellenmiyor
- Toast notifications görünmüyor
- Dashboard data stale

**Çözümler:**

#### 🔍 Çözüm 1: WebSocket Connection Check
```javascript
// WebSocket bağlantısını kontrol et
const ws = new WebSocket('ws://localhost:8001/ws');
ws.onopen = () => console.log('WebSocket connected');
ws.onerror = (error) => console.error('WebSocket error:', error);
```

#### 🔄 Çözüm 2: Frontend Service Restart
```bash
# Frontend development server'ı restart et
npm run dev
```

#### ⚙️ Çözüm 3: Cache Clear
```javascript
// Browser cache'i temizle
localStorage.clear();
sessionStorage.clear();
location.reload();
```

---

## 🔐 Güvenlik Sorunları

### 🚫 Sorun: AI Actions Blocked by Security

**Belirtiler:**
- "Operation denied" errors
- High-risk operations rejected
- Security violations logged

**Çözümler:**

#### ⚙️ Çözüm 1: Permission Configuration
```yaml
# .kiro/steering/ai-permissions.md
risk_tolerance: "medium"
auto_approve_safe: true
auto_approve_low: true
```

#### 🔍 Çözüm 2: Security Logs Check
```bash
# Security log'larını kontrol et
curl "http://localhost:8001/api/v1/security/logs?level=warning"
```

#### 🔄 Çözüm 3: Security Manager Reset
```bash
# Security manager'ı reset et
curl -X POST "http://localhost:8001/api/v1/security/reset"
```

---

## 🛠️ Genel Troubleshooting Adımları

### 1. 🔍 Sistem Durumu Kontrolü
```bash
# Kapsamlı sistem kontrolü
curl "http://localhost:8001/api/v1/health/" | jq '.'
```

### 2. 📊 AI Health Check
```bash
# AI sistem sağlık kontrolü
curl -X POST "http://localhost:8001/api/v1/ai/system/health-check"
```

### 3. 🚨 Alert Kontrolü
```bash
# Aktif alert'leri kontrol et
curl "http://localhost:8001/api/v1/monitoring/alerts"
```

### 4. 📈 Pattern Analysis
```bash
# Tespit edilen pattern'leri kontrol et
curl "http://localhost:8001/api/v1/monitoring/patterns"
```

### 5. 🔄 Service Restart Sequence
```bash
#!/bin/bash
# Tüm servisleri sırayla restart et

services=("database" "redis" "mcp-servers" "backend" "frontend")

for service in "${services[@]}"; do
  echo "Restarting $service..."
  docker restart $service
  sleep 10
done
```

## 📞 Destek Alma

Eğer bu rehberdeki çözümler sorununuzu çözmezse:

### 🤖 AI Destek
```bash
# AI'dan yardım iste
curl -X POST "http://localhost:8001/api/v1/ai/help" \
  -d '{"problem": "Describe your issue here"}'
```

### 📧 İnsan Destek
- **GitHub Issues**: [Issues](https://github.com/turtir-ai/mcp-ecosystem-platform/issues)
- **Email**: support@kairos.ai
- **Discord**: [Community Server](https://discord.gg/kairos-ai)

### 📋 Sorun Raporu Template
```markdown
## Sorun Açıklaması
[Sorunu detaylı açıklayın]

## Sistem Bilgileri
- OS: [İşletim sistemi]
- Docker Version: [Docker versiyonu]
- Platform Version: [Platform versiyonu]

## Hata Mesajları
```
[Hata mesajlarını buraya yapıştırın]
```

## Denenen Çözümler
- [ ] Çözüm 1
- [ ] Çözüm 2

## AI Analizi
```json
[AI analiz sonucunu buraya yapıştırın]
```
```

## 🔗 İlgili Dokümantasyon

- [AI API Documentation](AI_API_DOCUMENTATION.md)
- [Security Guide](SECURITY.md)
- [Installation Guide](INSTALLATION.md)
- [Configuration Guide](CONFIGURATION.md)