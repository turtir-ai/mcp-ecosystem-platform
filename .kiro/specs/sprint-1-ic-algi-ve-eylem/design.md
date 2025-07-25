# Sprint 1: İç Algı ve İlk Eylemler - Tasarım Belgesi

## Genel Bakış

Bu tasarım, AI Ekip Arkadaşının ilk gerçek "bilişsel kıvılcımlarını" oluşturacak sistem bileşenlerini tanımlar. AI artık sadece sistem durumunu okumakla kalmayacak, bu bilgiyi analiz edip anlamlı eylemlere dönüştürecek. Bu, "reaktif monitoring"den "proaktif AI partnership"e geçişin temelini oluşturur.

## Mimari

### Mevcut Sistem (Sprint 0 Sonrası)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│   Backend       │◄──►│ MCP Servers     │
│   Dashboard     │    │   Health API    │    │ (groq-llm, etc) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│ Health Display  │    │ Status Monitor  │
│ (Reactive)      │    │ (Passive)       │
└─────────────────┘    └─────────────────┘
```

### Yeni Sistem (Sprint 1 Sonrası)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│   Backend       │◄──►│ MCP Servers     │
│   Dashboard     │    │   Health API    │    │ (groq-llm, etc) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Smart Error     │    │ AI Diagnostics  │    │ LLM Analysis    │
│ Handler         │    │ Engine          │    │ (groq-llm)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ User-Friendly   │    │ Action          │    │ Learning        │
│ Messages        │    │ Recommendations │    │ Database        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Bileşenler ve Arayüzler

### 1. Smart Error Handler (Frontend)

**Konum**: `frontend/src/services/smartErrorHandler.ts`

**Amaç**: API hatalarını yakalayıp AI analizine gönderen akıllı hata yöneticisi

**Arayüz**:
```typescript
interface SmartErrorHandler {
  handleConnectionError(error: Error, context: RequestContext): Promise<SmartErrorResponse>;
  handleTimeoutError(error: Error, context: RequestContext): Promise<SmartErrorResponse>;
  handleServerError(error: Error, context: RequestContext): Promise<SmartErrorResponse>;
}

interface SmartErrorResponse {
  userFriendlyMessage: string;
  technicalDetails: string;
  suggestedActions: ActionSuggestion[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  canAutoFix: boolean;
}

interface ActionSuggestion {
  title: string;
  description: string;
  actionType: 'manual' | 'ai_assisted' | 'automatic';
  estimatedTime: string;
  riskLevel: 'safe' | 'low' | 'medium' | 'high';
}
```

### 2. AI Diagnostics Engine (Backend)

**Konum**: `backend/app/services/ai_diagnostics.py`

**Amaç**: Hataları ve sistem durumunu analiz eden AI motor

**Arayüz**:
```python
class AIDiagnosticsEngine:
    async def analyze_connection_error(
        self, 
        error_details: Dict[str, Any], 
        system_context: SystemContext
    ) -> DiagnosisResult:
        """Bağlantı hatalarını analiz eder"""
        pass
    
    async def analyze_performance_issue(
        self, 
        metrics: SystemMetrics, 
        historical_data: List[MetricSnapshot]
    ) -> DiagnosisResult:
        """Performans sorunlarını analiz eder"""
        pass
    
    async def suggest_remediation(
        self, 
        diagnosis: DiagnosisResult
    ) -> List[RemediationAction]:
        """Çözüm önerileri sunar"""
        pass

@dataclass
class DiagnosisResult:
    issue_type: str
    severity: str
    root_cause_analysis: str
    user_friendly_explanation: str
    confidence_score: float
    suggested_actions: List[str]
    learning_data: Dict[str, Any]
```

### 3. Proactive Monitor Enhancement

**Konum**: `backend/app/services/proactive_monitor.py` (Mevcut dosyayı genişletme)

**Yeni Özellikler**:
- AI-powered pattern detection
- Predictive issue identification
- Automated remediation suggestions

### 4. Smart Notification System (Frontend)

**Konum**: `frontend/src/services/smartNotifications.ts` (Mevcut dosyayı genişletme)

**Yeni Özellikler**:
```typescript
interface SmartNotification extends Notification {
  aiGenerated: boolean;
  actionable: boolean;
  suggestedActions: ActionSuggestion[];
  learnFromUserAction: boolean;
}

class SmartNotificationService {
  showAIAnalysis(analysis: DiagnosisResult): void;
  showActionSuggestion(suggestion: ActionSuggestion): void;
  trackUserResponse(notificationId: string, userAction: string): void;
}
```

## Veri Modelleri

### AI Analysis Data Models

```typescript
// Frontend Types
interface ErrorAnalysisRequest {
  errorType: string;
  errorMessage: string;
  stackTrace?: string;
  requestContext: {
    url: string;
    method: string;
    timestamp: Date;
    userAgent: string;
  };
  systemContext: {
    currentRoute: string;
    userActions: UserAction[];
    systemHealth: HealthStatus;
  };
}

interface AIInsight {
  id: string;
  type: 'error_analysis' | 'performance_suggestion' | 'proactive_warning';
  title: string;
  description: string;
  technicalDetails: string;
  suggestedActions: ActionSuggestion[];
  confidence: number;
  timestamp: Date;
  status: 'new' | 'acknowledged' | 'resolved' | 'dismissed';
}
```

```python
# Backend Models
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class SystemContext:
    current_health: Dict[str, Any]
    recent_errors: List[Dict[str, Any]]
    resource_usage: Dict[str, float]
    mcp_server_status: Dict[str, str]
    user_activity: List[Dict[str, Any]]

@dataclass
class LearningData:
    error_pattern: str
    solution_effectiveness: float
    user_satisfaction: Optional[int]
    resolution_time: Optional[float]
    similar_cases: List[str]

@dataclass
class RemediationAction:
    action_id: str
    title: str
    description: str
    action_type: str  # 'restart_service', 'clear_cache', 'check_config', etc.
    risk_level: str
    estimated_duration: str
    requires_approval: bool
    automation_script: Optional[str]
```

## AI Entegrasyonu

### LLM Prompt Engineering

**Error Analysis Prompt Template**:
```
Sistem Hatası Analizi:

Hata Detayları:
- Hata Türü: {error_type}
- Hata Mesajı: {error_message}
- Zaman: {timestamp}
- Bağlam: {context}

Sistem Durumu:
- Backend Sağlığı: {backend_health}
- MCP Sunucuları: {mcp_status}
- Kaynak Kullanımı: {resource_usage}

Lütfen şunları sağla:
1. Bu hatanın olası 3 ana nedeni (olasılık sırasına göre)
2. Her neden için kullanıcı dostu açıklama
3. Somut çözüm adımları
4. Benzer sorunları önleme önerileri

Yanıtını JSON formatında ver:
{
  "root_causes": [...],
  "user_explanation": "...",
  "solution_steps": [...],
  "prevention_tips": [...]
}
```

### MCP Tool Integration

**Yeni MCP Tools**:
```python
# AI Diagnostics MCP Tool
@mcp_tool
async def diagnose_system_issue(
    issue_description: str,
    system_context: Dict[str, Any]
) -> Dict[str, Any]:
    """AI-powered system issue diagnosis"""
    pass

@mcp_tool  
async def suggest_remediation(
    diagnosis_result: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate remediation suggestions"""
    pass

@mcp_tool
async def learn_from_resolution(
    issue_id: str,
    resolution_outcome: Dict[str, Any]
) -> bool:
    """Learn from issue resolution for future improvements"""
    pass
```

## Hata Yönetimi

### Graceful AI Failure Handling

1. **AI Service Unavailable**: Fallback to traditional error messages
2. **LLM Response Parsing Error**: Use structured fallback responses
3. **Analysis Timeout**: Provide immediate basic suggestions, continue analysis in background
4. **Confidence Too Low**: Combine AI suggestions with traditional troubleshooting

### Error Recovery Strategies

```typescript
class AIErrorRecovery {
  async handleAIServiceFailure(originalError: Error): Promise<ErrorResponse> {
    // Fallback to rule-based error handling
    return this.traditionalErrorHandler.handle(originalError);
  }
  
  async handleLowConfidenceAnalysis(analysis: DiagnosisResult): Promise<ErrorResponse> {
    // Combine AI insights with traditional solutions
    const traditionalSolutions = await this.getTraditionalSolutions(analysis.issue_type);
    return this.mergeAIAndTraditionalSolutions(analysis, traditionalSolutions);
  }
}
```

## Test Stratejisi

### Unit Tests
- AI diagnostics engine logic
- Error handler response formatting
- LLM prompt generation and parsing
- Fallback mechanism testing

### Integration Tests
- Frontend error → AI analysis → User notification flow
- Backend health issue → AI suggestion → User action flow
- MCP tool integration with AI diagnostics

### E2E Tests
- Complete AI-assisted error resolution workflow
- User interaction with AI suggestions
- Learning feedback loop validation

### AI-Specific Tests
- LLM response quality validation
- Confidence score accuracy
- Learning effectiveness measurement
- Prompt engineering optimization

## Performans Optimizasyonu

### AI Response Caching
- Cache common error analysis results
- Implement intelligent cache invalidation
- Use Redis for distributed caching

### Asynchronous Processing
- Background AI analysis for non-critical issues
- Queue system for batch processing
- Progressive enhancement of AI insights

### Resource Management
- LLM request rate limiting
- Token usage optimization
- Fallback to cached responses under load