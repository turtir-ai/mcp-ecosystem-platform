---
inclusion: always
---

# AI İzinleri ve Güvenlik Kuralları

Bu belge, AI'ın sistem üzerinde gerçekleştirebileceği eylemleri ve güvenlik sınırlarını tanımlar.

## Genel Prensipler

1. **Kullanıcı Onayı İlkesi**: Yüksek riskli işlemler mutlaka kullanıcı onayı gerektirir
2. **Şeffaflık İlkesi**: AI'ın tüm eylemleri loglanır ve izlenebilir
3. **En Az Yetki İlkesi**: AI sadece gerekli minimum yetkilerle çalışır
4. **Geri Alınabilirlik İlkesi**: Mümkün olan tüm işlemler geri alınabilir olmalı

## AI Eylem Kategorileri

### 🟢 Otomatik Onaylı (SAFE/LOW)
- Sistem durumu sorgulama (`get_system_health`)
- Log okuma (`mcp_server_logs`)
- Dosya okuma (sadece proje dizini içinde)
- Git status kontrolü

### 🟡 Kullanıcı Onayı Gerekli (MEDIUM)
- Dosya yazma/düzenleme
- Git commit/push işlemleri
- Otomatik düzeltme uygulama (`auto_fix_apply`)
- Konfigürasyon değişiklikleri

### 🔴 Yüksek Riskli - Açık Onay Gerekli (HIGH)
- MCP sunucu yeniden başlatma (`mcp_server_restart`)
- MCP sunucu durdurma (`mcp_server_stop`)
- Sistem konfigürasyonu değişiklikleri
- Güvenlik ayarları değişiklikleri

### ⛔ Yasaklı İşlemler (CRITICAL)
- Sistem kapatma/yeniden başlatma
- Veritabanı silme/format
- Kritik sistem dosyalarına erişim
- Root/admin yetki gerektiren işlemler

## MCP Sunucu Yönetimi Kuralları

### Restart İzinleri
```yaml
allowed_servers:
  - "groq-llm"
  - "openrouter-llm" 
  - "browser-automation"
  - "enhanced-filesystem"
  
restricted_servers:
  - "kiro-tools"      # Kritik sistem erişimi
  - "simple-warp"     # Terminal erişimi
  
approval_required: true
max_restarts_per_hour: 3
```

### Log Erişimi
```yaml
log_access:
  - level: "INFO"
    approval: false
  - level: "ERROR" 
    approval: false
  - level: "DEBUG"
    approval: true    # Detaylı sistem bilgisi
```

## Güvenlik Kontrolleri

### Komut Filtreleme
AI'ın çalıştırabileceği komutlar beyaz liste ile sınırlıdır:
- `docker ps`, `docker logs`
- `git status`, `git log`
- `npm install`, `pip install`
- Proje dizini içinde dosya işlemleri

### Yasaklı Komutlar
- `rm -rf`, `del /s`
- `sudo`, `chmod 777`
- `shutdown`, `reboot`
- `format`, `fdisk`

## Onay Süreci

### Otomatik Onay Koşulları
1. İşlem SAFE/LOW risk seviyesinde
2. Proje dizini içinde sınırlı
3. Geri alınabilir işlem
4. Kullanıcı daha önce benzer işlemi onaylamış

### Manuel Onay Gerektiren Durumlar
1. HIGH/CRITICAL risk seviyesi
2. Sistem genelinde etki
3. Geri alınamaz işlem
4. İlk kez yapılan işlem türü

### Onay Timeout
- HIGH risk: 5 dakika
- CRITICAL risk: 2 dakika
- Timeout sonrası otomatik red

## Monitoring ve Audit

### Loglanacak Bilgiler
- Eylem türü ve parametreleri
- Risk seviyesi ve gerekçesi
- Onay durumu ve onaylayan kullanıcı
- İşlem sonucu ve süre
- Hata durumları

### Uyarı Koşulları
- Saatte 5'ten fazla HIGH risk işlem
- Başarısız onay oranı %20'yi geçerse
- Kritik sistem dosyalarına erişim denemesi
- Anormal komut pattern'leri

## Acil Durum Prosedürleri

### AI Devre Dışı Bırakma
Şu durumlarda AI otomatik olarak devre dışı bırakılır:
- 3 başarısız CRITICAL işlem denemesi
- Güvenlik ihlali tespit edilmesi
- Sistem kaynaklarının %90'ını aşması
- Kullanıcı tarafından manuel durdurma

### Güvenlik İhlali Durumunda
1. Tüm AI işlemleri durdurulur
2. Güvenlik logları korunur
3. Kullanıcı bilgilendirilir
4. Manuel müdahale beklenir

## Konfigürasyon Örnekleri

### Geliştirme Ortamı
```yaml
environment: "development"
risk_tolerance: "medium"
auto_approve_safe: true
auto_approve_low: true
require_approval_medium: true
require_approval_high: true
block_critical: true
```

### Üretim Ortamı
```yaml
environment: "production"
risk_tolerance: "low"
auto_approve_safe: true
auto_approve_low: false
require_approval_medium: true
require_approval_high: true
block_critical: true
```