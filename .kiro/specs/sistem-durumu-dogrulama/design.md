# Tasarım Belgesi

## Genel Bakış

Bu tasarım, MCP Ecosystem Platform'un temel bileşenlerinin (backend FastAPI servisi ve frontend React uygulaması) durumunu doğrulamak ve izlemek için gerekli sistem bileşenlerini tanımlar. Sistem, mevcut çalışan servisleri tespit ederek durumlarını raporlar ve gelecekteki geliştirmeler için sağlam bir temel sağlar.

## Mimari

### Mevcut Sistem Durumu
- **Backend**: FastAPI servisi (port 8000) - ÇALIŞİYOR
- **Frontend**: React geliştirme sunucusu (port 3000) - ÇALIŞİYOR
- **Mock API Server**: Python sunucusu (port 8009) - MCP sunucu yöneticisi

### Sistem Durumu Doğrulama Mimarisi

```
┌─────────────────┐    HTTP/API    ┌─────────────────┐
│   Frontend      │◄──────────────►│   Backend       │
│   (React)       │                │   (FastAPI)     │
│   Port: 3000    │                │   Port: 8000    │
└─────────────────┘                └─────────────────┘
         │                                   │
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│ Status Monitor  │                │ Health Endpoint │
│ Component       │                │ /health         │
└─────────────────┘                └─────────────────┘
```

## Bileşenler ve Arayüzler

### 1. Akıllı Backend Health Endpoint
- **Endpoint**: `GET /health`
- **Amaç**: AI'ın eyleme geçebilmesi için zenginleştirilmiş sistem durumu bilgileri
- **Response Format**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-24T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": {
      "status": "connected",
      "latency_ms": 45,
      "connection_pool_active": 3
    },
    "mcp_servers": {
      "status": "active",
      "active_count": 5,
      "total_count": 6,
      "unhealthy_servers": ["simple-warp"]
    }
  },
  "resource_usage": {
    "cpu_percent": 12.5,
    "memory_percent": 34.2,
    "disk_usage_percent": 67.8
  },
  "actionable_insights": [
    {
      "type": "warning",
      "message": "simple-warp server is unresponsive",
      "suggested_action": "restart_mcp_server",
      "server_name": "simple-warp"
    }
  ]
}
```

### 2. AI Eylem Endpoint'leri
- **Endpoint**: `POST /api/v1/mcp/restart/{server_name}`
- **Amaç**: AI'ın sağlıksız MCP sunucularını yeniden başlatabilmesi
- **Security**: Kullanıcı onayı gerektirir

- **Endpoint**: `GET /api/v1/mcp/logs/{server_name}`
- **Amaç**: AI'ın sorun teşhisi için log analizi yapabilmesi
- **Response**: Son 100 log satırı ve hata analizi

### 2. Frontend Status Component
- **Konum**: `src/components/SystemStatus/`
- **Amaç**: Backend bağlantısını test eder ve sistem durumunu görüntüler
- **Özellikler**:
  - Backend bağlantı testi
  - Servis durumu göstergesi
  - Sürüm bilgisi görüntüleme

### 3. MCP Server Status Integration
- **Mevcut Bileşen**: `MCPStatusTable.tsx` (zaten mevcut)
- **Geliştirme**: Mock API server ile entegrasyon

## Veri Modelleri

### Zenginleştirilmiş Veri Modelleri

```typescript
interface MCPServerHealth extends MCPServerStatus {
  pid?: number;
  memoryUsageMb?: number;
  cpuUsagePercent?: number;
  lastHeartbeat?: Date;
  errorCount?: number;
}

interface ActionableInsight {
  type: 'info' | 'warning' | 'error';
  message: string;
  suggested_action?: 'restart_mcp_server' | 'check_logs' | 'restart_backend';
  server_name?: string;
  priority: 'low' | 'medium' | 'high';
}

interface SystemStatus {
  backend: {
    status: 'healthy' | 'unhealthy' | 'unknown';
    url: string;
    version?: string;
    lastChecked: Date;
    resourceUsage?: {
      cpu_percent: number;
      memory_percent: number;
      disk_usage_percent: number;
    };
  };
  frontend: {
    status: 'running';
    version: string;
  };
  mcpServers: MCPServerHealth[];
  actionableInsights: ActionableInsight[];
}

interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version: string;
  services: {
    database: {
      status: string;
      latency_ms: number;
      connection_pool_active: number;
    };
    mcp_servers: {
      status: string;
      active_count: number;
      total_count: number;
      unhealthy_servers: string[];
    };
  };
  resource_usage: {
    cpu_percent: number;
    memory_percent: number;
    disk_usage_percent: number;
  };
  actionable_insights: ActionableInsight[];
}
```

## Hata Yönetimi

### Backend Bağlantı Hataları
- **Timeout**: 5 saniye sonra bağlantı hatası
- **Network Error**: Ağ bağlantısı sorunu bildirimi
- **Server Error**: 5xx hataları için genel hata mesajı

### Frontend Hata Gösterimi
- Toast bildirimleri ile kullanıcı bilgilendirmesi
- Status indicator'lar ile görsel durum gösterimi
- Retry mekanizması ile otomatik yeniden deneme

## Test Stratejisi

### Unit Tests
- Health endpoint response formatı testi
- Status component render testi
- Error handling testi

### Integration Tests
- Frontend-Backend API bağlantı testi
- MCP server status entegrasyon testi
- End-to-end sistem durumu testi

### Manual Testing
- Servisleri kapatıp açarak hata durumlarını test etme
- Farklı port konfigürasyonları ile test etme
- Network kesintisi simülasyonu