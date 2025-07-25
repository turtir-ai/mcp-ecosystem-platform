# 🤖 AI Action API Documentation

Bu dokümantasyon, MCP Ecosystem Platform'un AI destekli sistem yönetimi API'lerini detaylı olarak açıklar.

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Kimlik Doğrulama](#kimlik-doğrulama)
- [AI Eylem Endpoint'leri](#ai-eylem-endpointleri)
- [Sistem Sağlığı API'leri](#sistem-sağlığı-apileri)
- [Proaktif İzleme API'leri](#proaktif-izleme-apileri)
- [Güvenlik API'leri](#güvenlik-apileri)
- [Hata Kodları](#hata-kodları)
- [Örnekler](#örnekler)

## 🌟 Genel Bakış

AI Action API'leri, sistem yönetimi görevlerini AI aracılığıyla gerçekleştirmek için tasarlanmıştır. Tüm AI eylemleri güvenlik kontrolleri ve onay mekanizmaları ile korunmaktadır.

### Base URL
```
https://your-domain.com/api/v1
```

### Response Format
Tüm API yanıtları standart format kullanır:

```json
{
  "success": boolean,
  "data": object | array | null,
  "error": string | null,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "uuid",
  "execution_time_ms": number
}
```

## 🔐 Kimlik Doğrulama

API'ler şu kimlik doğrulama yöntemlerini destekler:

### Bearer Token
```http
Authorization: Bearer <your-token>
```

### API Key
```http
X-API-Key: <your-api-key>
```

## 🤖 AI Eylem Endpoint'leri

### MCP Sunucu Yeniden Başlatma

AI tarafından MCP sunucu yeniden başlatma işlemi.

```http
POST /ai/mcp/restart/{server_name}
```

#### Parameters
- `server_name` (path): Yeniden başlatılacak sunucu adı
- `reasoning` (query, optional): AI'ın gerekçesi

#### Request Example
```bash
curl -X POST "https://api.example.com/api/v1/ai/mcp/restart/groq-llm?reasoning=Server%20appears%20unresponsive" \
  -H "Authorization: Bearer <token>"
```

#### Response Examples

**Onay Gerekli (200 OK)**
```json
{
  "success": false,
  "error": "User approval required",
  "data": {
    "approval_required": true,
    "approval_request": {
      "operation_id": "op-123e4567-e89b-12d3-a456-426614174000",
      "operation_type": "mcp_server_restart",
      "parameters": {
        "server_name": "groq-llm"
      },
      "risk_level": "high",
      "reason": "High risk operation requires approval",
      "ai_reasoning": "Server appears unresponsive",
      "status": "pending",
      "requester": "AI_AGENT",
      "timeout_minutes": 5,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }
}
```

**Başarılı (200 OK)**
```json
{
  "success": true,
  "data": {
    "message": "Server groq-llm restart initiated by AI",
    "reasoning": "Server appears unresponsive"
  }
}
```

### MCP Sunucu Durdurma

```http
POST /ai/mcp/stop/{server_name}
```

#### Parameters
- `server_name` (path): Durdurulacak sunucu adı
- `reasoning` (query, optional): AI'ın gerekçesi

### MCP Sunucu Log Erişimi

```http
GET /ai/mcp/logs/{server_name}
```

#### Parameters
- `server_name` (path): Log'ları alınacak sunucu adı
- `lines` (query, optional): Alınacak log satır sayısı (default: 100)

#### Response Example
```json
{
  "success": true,
  "data": {
    "server_name": "groq-llm",
    "log_lines": [
      "[INFO] 2024-01-15T10:25:00Z - Server started successfully",
      "[WARN] 2024-01-15T10:26:00Z - High response time detected",
      "[ERROR] 2024-01-15T10:27:00Z - Connection timeout to external service"
    ],
    "total_lines": 3,
    "analysis": {
      "error_count": 1,
      "warning_count": 1,
      "last_error": "Connection timeout to external service",
      "status": "recovering"
    }
  }
}
```

### Sistem Sağlık Kontrolü

AI tarafından kapsamlı sistem sağlık kontrolü.

```http
POST /ai/system/health-check
```

#### Parameters
- `reasoning` (query, optional): AI'ın gerekçesi

#### Response Example
```json
{
  "success": true,
  "data": {
    "timestamp": "2024-01-15T10:30:00Z",
    "system_metrics": {
      "cpu_percent": 45.2,
      "memory_percent": 67.8,
      "disk_percent": 23.4,
      "process_count": 156,
      "load_average": [0.5, 0.7, 0.9]
    },
    "mcp_server_count": 11,
    "healthy_servers": 9,
    "health_issues": [
      {
        "type": "mcp_server",
        "server": "openrouter-llm",
        "status": "DEGRADED",
        "issue": "High response time"
      }
    ],
    "recommendations": [
      {
        "action": "investigate_processes",
        "target": "openrouter-llm",
        "priority": "medium",
        "reason": "Server showing degraded performance"
      }
    ],
    "overall_status": "degraded",
    "ai_reasoning": "Routine health check"
  }
}
```

### Süreç Araştırması

```http
POST /ai/system/investigate-processes
```

#### Response Example
```json
{
  "success": true,
  "data": {
    "timestamp": "2024-01-15T10:30:00Z",
    "top_processes": [
      {
        "pid": 1234,
        "name": "python",
        "cpu_percent": 15.5,
        "memory_percent": 8.2
      }
    ],
    "analysis": {
      "high_cpu_processes": [...],
      "high_memory_processes": [...],
      "total_processes": 156,
      "system_load": [1.2, 1.5, 1.8]
    },
    "recommendations": [
      {
        "type": "performance",
        "message": "Found 2 high CPU processes",
        "suggestion": "Consider restarting or optimizing high CPU processes",
        "priority": "medium"
      }
    ]
  }
}
```

## 🏥 Sistem Sağlığı API'leri

### Kapsamlı Sistem Sağlığı

```http
GET /health/
```

#### Response Example
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "services": {
      "database": {
        "status": "connected",
        "latency_ms": 45.2,
        "connection_pool_active": 3,
        "connection_pool_max": 10
      },
      "mcp_servers": {
        "status": "active",
        "active_count": 10,
        "total_count": 11,
        "unhealthy_servers": ["openrouter-llm"],
        "server_details": {
          "groq-llm": {
            "status": "HEALTHY",
            "response_time_ms": 120,
            "uptime_percentage": 99.5,
            "last_check": "2024-01-15T10:29:00Z"
          }
        }
      }
    },
    "resource_usage": {
      "cpu_percent": 45.2,
      "memory_percent": 67.8,
      "disk_usage_percent": 23.4,
      "memory_available_gb": 2.1,
      "disk_free_gb": 150.5,
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "actionable_insights": [
      {
        "id": "insight-123",
        "type": "warning",
        "message": "MCP server openrouter-llm has degraded performance",
        "suggested_action": "investigate_processes",
        "server_name": "openrouter-llm",
        "priority": "medium",
        "can_auto_fix": true,
        "risk_level": "low",
        "reasoning": "Response time is 3x normal threshold",
        "confidence_score": 85,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "system_recommendations": [
      {
        "id": "rec-456",
        "type": "performance",
        "message": "Consider optimizing openrouter-llm server",
        "suggestion": "Restart server or investigate resource usage",
        "priority": "medium",
        "estimated_impact": "Improved response times",
        "implementation_time": "2-5 minutes"
      }
    ],
    "health_score": 85,
    "uptime_seconds": 86400,
    "environment": "production"
  }
}
```

### Basit Sağlık Kontrolü

```http
GET /health/simple
```

#### Response Example
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "mcp-ecosystem-platform"
}
```

## 📊 Proaktif İzleme API'leri

### Aktif Uyarıları Getir

```http
GET /monitoring/alerts
```

#### Response Example
```json
{
  "success": true,
  "data": [
    {
      "id": "alert-789",
      "severity": "warning",
      "title": "High CPU Usage Detected",
      "message": "System CPU usage is at 88.5%",
      "timestamp": "2024-01-15T10:25:00Z",
      "source": "system_resources",
      "metadata": {
        "cpu_percent": 88.5
      },
      "suggested_actions": [
        "investigate_processes",
        "restart_services",
        "resource_optimization"
      ],
      "acknowledged": false,
      "resolved": false,
      "auto_resolve": false
    }
  ]
}
```

### Uyarı Onaylama

```http
POST /monitoring/alerts/{alert_id}/acknowledge
```

### Uyarı Çözme

```http
POST /monitoring/alerts/{alert_id}/resolve
```

### Tespit Edilen Pattern'leri Getir

```http
GET /monitoring/patterns
```

#### Response Example
```json
{
  "success": true,
  "data": [
    {
      "pattern_type": "recurring_failure",
      "description": "Server groq-llm has recurring failures every 2 hours",
      "confidence": 0.85,
      "first_occurrence": "2024-01-15T02:00:00Z",
      "last_occurrence": "2024-01-15T10:00:00Z",
      "frequency": 4,
      "affected_components": ["groq-llm"],
      "suggested_resolution": "Investigate root cause and consider server replacement",
      "metadata": {
        "server_name": "groq-llm",
        "failure_frequency": 0.5,
        "failure_count": 4
      }
    }
  ]
}
```

### Bağlantı Kaybı Analizi

```http
POST /monitoring/analyze-connection-loss
```

#### Request Body
```json
{
  "component": "Backend API",
  "error_details": "Connection refused on port 8000"
}
```

#### Response Example
```json
{
  "success": true,
  "data": {
    "component": "Backend API",
    "error_details": "Connection refused on port 8001",
    "timestamp": "2024-01-15T10:30:00Z",
    "possible_causes": [
      "Service is not running",
      "Port is blocked or changed"
    ],
    "suggested_solutions": [
      "restart_service",
      "check_port_configuration"
    ],
    "confidence": 0.8
  }
}
```

## 🔐 Güvenlik API'leri

### Bekleyen Onayları Getir

```http
GET /security/approvals
```

#### Response Example
```json
{
  "success": true,
  "data": [
    {
      "operation_id": "op-123e4567-e89b-12d3-a456-426614174000",
      "operation_type": "mcp_server_restart",
      "parameters": {
        "server_name": "groq-llm"
      },
      "risk_level": "high",
      "reason": "High risk operation requires approval",
      "ai_reasoning": "Server appears unresponsive",
      "timestamp": "2024-01-15T10:30:00Z",
      "status": "pending",
      "requester": "AI_AGENT",
      "timeout_minutes": 5,
      "affected_systems": ["groq-llm"],
      "rollback_plan": "Restart can be reversed by stopping the server",
      "estimated_duration": "2-3 minutes"
    }
  ]
}
```

### İşlemi Onaylama

```http
POST /security/approve/{operation_id}
```

#### Parameters
- `user_id` (query, optional): Onaylayan kullanıcı ID'si

### İşlemi Reddetme

```http
POST /security/reject/{operation_id}
```

#### Parameters
- `user_id` (query, optional): Reddeden kullanıcı ID'si
- `reason` (query, optional): Red gerekçesi

## ❌ Hata Kodları

### HTTP Status Codes

| Kod | Açıklama |
|-----|----------|
| 200 | Başarılı |
| 400 | Geçersiz istek |
| 401 | Kimlik doğrulama hatası |
| 403 | Yetki hatası |
| 404 | Kaynak bulunamadı |
| 429 | Rate limit aşıldı |
| 500 | Sunucu hatası |

### AI-Specific Error Codes

| Kod | Mesaj | Açıklama |
|-----|-------|----------|
| AI001 | Approval required | İşlem için kullanıcı onayı gerekli |
| AI002 | Operation denied | İşlem güvenlik kuralları tarafından reddedildi |
| AI003 | Risk level too high | İşlem risk seviyesi çok yüksek |
| AI004 | Server not found | Belirtilen MCP sunucusu bulunamadı |
| AI005 | Operation timeout | İşlem zaman aşımına uğradı |

## 📝 Örnekler

### Tam AI Workflow Örneği

```bash
#!/bin/bash

# 1. Sistem sağlığını kontrol et
HEALTH_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.example.com/api/v1/health/")

# 2. Sorunlu sunucu tespit et
SERVER_NAME=$(echo $HEALTH_RESPONSE | jq -r '.data.services.mcp_servers.unhealthy_servers[0]')

if [ "$SERVER_NAME" != "null" ]; then
  echo "Unhealthy server detected: $SERVER_NAME"
  
  # 3. AI restart öner
  RESTART_RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "https://api.example.com/api/v1/ai/mcp/restart/$SERVER_NAME?reasoning=Detected%20by%20health%20check")
  
  # 4. Onay gerekli mi kontrol et
  APPROVAL_REQUIRED=$(echo $RESTART_RESPONSE | jq -r '.data.approval_required')
  
  if [ "$APPROVAL_REQUIRED" = "true" ]; then
    OPERATION_ID=$(echo $RESTART_RESPONSE | jq -r '.data.approval_request.operation_id')
    echo "Approval required for operation: $OPERATION_ID"
    
    # 5. İşlemi onayla
    curl -X POST -H "Authorization: Bearer $TOKEN" \
      "https://api.example.com/api/v1/security/approve/$OPERATION_ID"
    
    echo "Operation approved"
  fi
fi
```

### JavaScript/TypeScript Örneği

```typescript
import axios from 'axios';

class AISystemManager {
  private baseURL = 'https://api.example.com/api/v1';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  private get headers() {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };
  }

  async checkSystemHealth() {
    const response = await axios.get(`${this.baseURL}/health/`, {
      headers: this.headers
    });
    return response.data;
  }

  async restartMCPServer(serverName: string, reasoning?: string) {
    const params = reasoning ? { reasoning } : {};
    const response = await axios.post(
      `${this.baseURL}/ai/mcp/restart/${serverName}`,
      {},
      { headers: this.headers, params }
    );
    return response.data;
  }

  async handleApprovalWorkflow(operationId: string) {
    // Onay ver
    const response = await axios.post(
      `${this.baseURL}/security/approve/${operationId}`,
      {},
      { headers: this.headers }
    );
    return response.data;
  }

  async monitorAlerts() {
    const response = await axios.get(`${this.baseURL}/monitoring/alerts`, {
      headers: this.headers
    });
    return response.data;
  }
}

// Kullanım örneği
const aiManager = new AISystemManager('your-token');

async function handleSystemIssue() {
  try {
    // Sistem sağlığını kontrol et
    const health = await aiManager.checkSystemHealth();
    
    // Sorunlu sunucuları tespit et
    const unhealthyServers = health.data.services.mcp_servers.unhealthy_servers;
    
    for (const serverName of unhealthyServers) {
      console.log(`Attempting to restart ${serverName}`);
      
      const restartResult = await aiManager.restartMCPServer(
        serverName, 
        'Detected by automated health check'
      );
      
      if (restartResult.data?.approval_required) {
        const operationId = restartResult.data.approval_request.operation_id;
        console.log(`Approving operation: ${operationId}`);
        
        await aiManager.handleApprovalWorkflow(operationId);
      }
    }
  } catch (error) {
    console.error('Error handling system issue:', error);
  }
}
```

### Python Örneği

```python
import requests
import json
from typing import Dict, List, Optional

class AISystemManager:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def check_system_health(self) -> Dict:
        """Sistem sağlığını kontrol et"""
        response = requests.get(
            f'{self.base_url}/health/',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def restart_mcp_server(self, server_name: str, reasoning: Optional[str] = None) -> Dict:
        """MCP sunucusunu yeniden başlat"""
        params = {'reasoning': reasoning} if reasoning else {}
        response = requests.post(
            f'{self.base_url}/ai/mcp/restart/{server_name}',
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def approve_operation(self, operation_id: str) -> Dict:
        """İşlemi onayla"""
        response = requests.post(
            f'{self.base_url}/security/approve/{operation_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_active_alerts(self) -> List[Dict]:
        """Aktif uyarıları getir"""
        response = requests.get(
            f'{self.base_url}/monitoring/alerts',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['data']

# Kullanım örneği
def main():
    ai_manager = AISystemManager(
        base_url='https://api.example.com/api/v1',
        token='your-token'
    )
    
    # Sistem sağlığını kontrol et
    health = ai_manager.check_system_health()
    print(f"System status: {health['data']['status']}")
    
    # Sorunlu sunucuları tespit et ve restart et
    unhealthy_servers = health['data']['services']['mcp_servers']['unhealthy_servers']
    
    for server_name in unhealthy_servers:
        print(f"Restarting {server_name}...")
        
        restart_result = ai_manager.restart_mcp_server(
            server_name, 
            'Detected by automated health check'
        )
        
        if restart_result.get('data', {}).get('approval_required'):
            operation_id = restart_result['data']['approval_request']['operation_id']
            print(f"Approving operation: {operation_id}")
            ai_manager.approve_operation(operation_id)
    
    # Aktif uyarıları kontrol et
    alerts = ai_manager.get_active_alerts()
    print(f"Active alerts: {len(alerts)}")

if __name__ == '__main__':
    main()
```

## 🔗 İlgili Dokümantasyon

- [AI Permissions Guide](../docs/AI_PERMISSIONS.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- [Security Best Practices](../docs/SECURITY.md)
- [MCP Server Management](../docs/MCP_SERVERS.md)

## 📞 Destek

API ile ilgili sorularınız için:
- **GitHub Issues**: [Issues](https://github.com/turtir-ai/mcp-ecosystem-platform/issues)
- **Documentation**: [Wiki](https://github.com/turtir-ai/mcp-ecosystem-platform/wiki)
- **Email**: support@kairos.ai