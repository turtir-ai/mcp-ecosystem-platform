"""
AI Diagnostics Engine - AI-powered system issue analysis and remediation suggestions

Bu servis, sistem hatalarını ve performans sorunlarını AI ile analiz eder,
kullanıcı dostu açıklamalar ve somut çözüm önerileri sunar.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    MANUAL = "manual"
    AI_ASSISTED = "ai_assisted"
    AUTOMATIC = "automatic"


@dataclass
class SystemContext:
    """Sistem durumu bağlamı"""
    current_health: Dict[str, Any]
    recent_errors: List[Dict[str, Any]]
    resource_usage: Dict[str, float]
    mcp_server_status: Dict[str, str]
    user_activity: List[Dict[str, Any]]
    timestamp: datetime


@dataclass
class RemediationAction:
    """Çözüm eylemi"""
    action_id: str
    title: str
    description: str
    action_type: ActionType
    risk_level: str
    estimated_duration: str
    requires_approval: bool
    steps: Optional[List[str]] = None
    automation_script: Optional[str] = None


@dataclass
class DiagnosisResult:
    """AI tanı sonucu"""
    issue_type: str
    severity: IssueSeverity
    root_cause_analysis: str
    user_friendly_explanation: str
    confidence_score: float
    suggested_actions: List[RemediationAction]
    learning_data: Dict[str, Any]
    timestamp: datetime


@dataclass
class LearningData:
    """AI öğrenme verisi"""
    error_pattern: str
    solution_effectiveness: float
    user_satisfaction: Optional[int]
    resolution_time: Optional[float]
    similar_cases: List[str]


class AIDiagnosticsEngine:
    """AI Tanı Motoru"""
    
    def __init__(self):
        self.diagnosis_cache: Dict[str, DiagnosisResult] = {}
        self.learning_database: List[LearningData] = []
        self.pattern_recognition_data: Dict[str, Any] = {}
        
    async def analyze_connection_error(
        self, 
        error_details: Dict[str, Any], 
        system_context: SystemContext
    ) -> DiagnosisResult:
        """Bağlantı hatalarını analiz eder"""
        
        error_type = error_details.get('error_type', 'unknown')
        error_message = error_details.get('error_message', '')
        request_url = error_details.get('request_context', {}).get('url', '')
        
        # Cache key oluştur
        cache_key = f"connection_{error_type}_{hash(error_message)}"
        
        if cache_key in self.diagnosis_cache:
            cached_result = self.diagnosis_cache[cache_key]
            # Cache'deki sonuç 5 dakikadan eskiyse yenile
            if (datetime.now() - cached_result.timestamp).seconds < 300:
                return cached_result
        
        try:
            # AI analizi için prompt hazırla
            analysis_prompt = self._build_connection_error_prompt(
                error_details, system_context
            )
            
            # LLM'den analiz al
            ai_response = await self._query_llm(analysis_prompt)
            
            # AI yanıtını parse et
            parsed_response = self._parse_ai_response(ai_response)
            
            # Tanı sonucunu oluştur
            diagnosis = DiagnosisResult(
                issue_type="connection_error",
                severity=self._determine_severity(error_details, system_context),
                root_cause_analysis=parsed_response.get('root_cause', 'Connection failed'),
                user_friendly_explanation=parsed_response.get('user_explanation', 
                    self._get_default_connection_explanation(error_type)),
                confidence_score=parsed_response.get('confidence', 0.7),
                suggested_actions=self._build_remediation_actions(
                    parsed_response.get('solutions', []), error_type
                ),
                learning_data={
                    'error_pattern': f"{error_type}_{error_message[:50]}",
                    'system_state': asdict(system_context),
                    'analysis_method': 'ai_llm'
                },
                timestamp=datetime.now()
            )
            
            # Cache'e kaydet
            self.diagnosis_cache[cache_key] = diagnosis
            
            return diagnosis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # Fallback analizi döndür
            return self._get_fallback_connection_diagnosis(error_details, system_context)
    
    async def analyze_performance_issue(
        self, 
        metrics: Dict[str, float], 
        historical_data: List[Dict[str, Any]]
    ) -> DiagnosisResult:
        """Performans sorunlarını analiz eder"""
        
        # Performans metriklerini değerlendir
        cpu_usage = metrics.get('cpu_percent', 0)
        memory_usage = metrics.get('memory_percent', 0)
        disk_usage = metrics.get('disk_usage_percent', 0)
        
        # Trend analizi
        trend_analysis = self._analyze_performance_trends(historical_data)
        
        # AI analizi için prompt hazırla
        analysis_prompt = self._build_performance_analysis_prompt(
            metrics, historical_data, trend_analysis
        )
        
        try:
            # LLM'den analiz al
            ai_response = await self._query_llm(analysis_prompt)
            parsed_response = self._parse_ai_response(ai_response)
            
            # Severity belirleme
            severity = IssueSeverity.LOW
            if cpu_usage > 80 or memory_usage > 85:
                severity = IssueSeverity.HIGH
            elif cpu_usage > 60 or memory_usage > 70:
                severity = IssueSeverity.MEDIUM
            
            diagnosis = DiagnosisResult(
                issue_type="performance_issue",
                severity=severity,
                root_cause_analysis=parsed_response.get('root_cause', 
                    f"High resource usage: CPU {cpu_usage}%, Memory {memory_usage}%"),
                user_friendly_explanation=parsed_response.get('user_explanation',
                    self._get_default_performance_explanation(metrics)),
                confidence_score=parsed_response.get('confidence', 0.8),
                suggested_actions=self._build_performance_remediation_actions(
                    metrics, parsed_response.get('solutions', [])
                ),
                learning_data={
                    'metrics': metrics,
                    'trend_analysis': trend_analysis,
                    'analysis_method': 'ai_performance'
                },
                timestamp=datetime.now()
            )
            
            return diagnosis
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return self._get_fallback_performance_diagnosis(metrics)
    
    async def suggest_remediation(
        self, 
        diagnosis: DiagnosisResult
    ) -> List[RemediationAction]:
        """Çözüm önerileri sunar"""
        
        # Mevcut öneriler varsa onları döndür
        if diagnosis.suggested_actions:
            return diagnosis.suggested_actions
        
        # AI'dan ek öneriler al
        try:
            remediation_prompt = self._build_remediation_prompt(diagnosis)
            ai_response = await self._query_llm(remediation_prompt)
            parsed_response = self._parse_ai_response(ai_response)
            
            additional_actions = self._build_remediation_actions(
                parsed_response.get('solutions', []), 
                diagnosis.issue_type
            )
            
            return additional_actions
            
        except Exception as e:
            logger.error(f"Remediation suggestion failed: {e}")
            return self._get_default_remediation_actions(diagnosis.issue_type)
    
    async def learn_from_resolution(
        self, 
        issue_id: str, 
        resolution_outcome: Dict[str, Any]
    ) -> bool:
        """Çözüm sonucundan öğrenir"""
        
        try:
            learning_data = LearningData(
                error_pattern=resolution_outcome.get('error_pattern', ''),
                solution_effectiveness=resolution_outcome.get('effectiveness', 0.0),
                user_satisfaction=resolution_outcome.get('user_satisfaction'),
                resolution_time=resolution_outcome.get('resolution_time'),
                similar_cases=resolution_outcome.get('similar_cases', [])
            )
            
            self.learning_database.append(learning_data)
            
            # Pattern recognition verilerini güncelle
            self._update_pattern_recognition(learning_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Learning from resolution failed: {e}")
            return False
    
    # Private helper methods
    
    def _build_connection_error_prompt(
        self, 
        error_details: Dict[str, Any], 
        system_context: SystemContext
    ) -> str:
        """Bağlantı hatası analizi için prompt oluşturur"""
        
        return f"""
Sistem Bağlantı Hatası Analizi:

Hata Detayları:
- Hata Türü: {error_details.get('error_type', 'unknown')}
- Hata Mesajı: {error_details.get('error_message', '')}
- İstek URL'si: {error_details.get('request_context', {}).get('url', '')}
- Zaman: {datetime.now().isoformat()}

Sistem Durumu:
- MCP Sunucuları: {system_context.mcp_server_status}
- Kaynak Kullanımı: {system_context.resource_usage}
- Son Hatalar: {len(system_context.recent_errors)} hata

Lütfen şunları analiz et:
1. Bu hatanın en olası 3 nedeni (olasılık sırasına göre)
2. Her neden için kullanıcı dostu açıklama
3. Somut çözüm adımları (kolay olanlar önce)
4. Benzer sorunları önleme önerileri

Yanıtını JSON formatında ver:
{{
  "root_cause": "Ana neden açıklaması",
  "user_explanation": "Kullanıcı dostu açıklama",
  "confidence": 0.85,
  "solutions": [
    {{
      "title": "Çözüm başlığı",
      "description": "Detaylı açıklama",
      "steps": ["Adım 1", "Adım 2"],
      "risk_level": "safe|low|medium|high",
      "estimated_time": "Tahmini süre"
    }}
  ]
}}
"""
    
    def _build_performance_analysis_prompt(
        self, 
        metrics: Dict[str, float], 
        historical_data: List[Dict[str, Any]], 
        trend_analysis: Dict[str, Any]
    ) -> str:
        """Performans analizi için prompt oluşturur"""
        
        return f"""
Sistem Performans Analizi:

Mevcut Metrikler:
- CPU Kullanımı: {metrics.get('cpu_percent', 0)}%
- Bellek Kullanımı: {metrics.get('memory_percent', 0)}%
- Disk Kullanımı: {metrics.get('disk_usage_percent', 0)}%

Trend Analizi:
{json.dumps(trend_analysis, indent=2)}

Geçmiş Veri Noktaları: {len(historical_data)}

Lütfen şunları analiz et:
1. Performans sorunun ana nedeni
2. Trend analizi sonuçları
3. Kritiklik seviyesi
4. Optimizasyon önerileri

Yanıtını JSON formatında ver:
{{
  "root_cause": "Performans sorunun ana nedeni",
  "user_explanation": "Kullanıcı dostu açıklama",
  "confidence": 0.90,
  "solutions": [
    {{
      "title": "Optimizasyon önerisi",
      "description": "Detaylı açıklama",
      "steps": ["Adım 1", "Adım 2"],
      "risk_level": "safe",
      "estimated_time": "5 dakika"
    }}
  ]
}}
"""
    
    def _build_remediation_prompt(self, diagnosis: DiagnosisResult) -> str:
        """Çözüm önerileri için prompt oluşturur"""
        
        return f"""
Çözüm Önerileri Geliştirme:

Tanı Sonucu:
- Sorun Türü: {diagnosis.issue_type}
- Severity: {diagnosis.severity.value}
- Ana Neden: {diagnosis.root_cause_analysis}
- Güven Skoru: {diagnosis.confidence_score}

Mevcut Öneriler: {len(diagnosis.suggested_actions)}

Lütfen ek çözüm önerileri geliştir:
1. Otomatik çözümler (risk seviyesi düşük)
2. AI destekli çözümler
3. Manuel çözümler (adım adım)

Yanıtını JSON formatında ver:
{{
  "solutions": [
    {{
      "title": "Çözüm başlığı",
      "description": "Detaylı açıklama",
      "action_type": "automatic|ai_assisted|manual",
      "steps": ["Adım 1", "Adım 2"],
      "risk_level": "safe|low|medium|high",
      "estimated_time": "Tahmini süre",
      "requires_approval": true/false
    }}
  ]
}}
"""
    
    async def _query_llm(self, prompt: str) -> str:
        """LLM'ye sorgu gönderir"""
        
        try:
            # MCP groq-llm tool'unu kullan
            from ..services.mcp_tools import call_mcp_tool
            
            result = await call_mcp_tool(
                server_name="groq-llm",
                tool_name="groq_generate",
                parameters={
                    "prompt": prompt,
                    "model": "llama-3.1-70b-versatile",
                    "max_tokens": 1024,
                    "temperature": 0.3
                }
            )
            
            return result.get('content', '')
            
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            raise
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """AI yanıtını parse eder"""
        
        try:
            # JSON yanıtı parse et
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # JSON olmayan yanıtları işle
            return {
                'root_cause': 'AI analysis completed',
                'user_explanation': response[:200],
                'confidence': 0.6,
                'solutions': []
            }
            
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI response: {response[:100]}")
            return {
                'root_cause': 'Analysis completed with limited data',
                'user_explanation': 'AI provided general analysis',
                'confidence': 0.5,
                'solutions': []
            }
    
    def _determine_severity(
        self, 
        error_details: Dict[str, Any], 
        system_context: SystemContext
    ) -> IssueSeverity:
        """Hata severity'sini belirler"""
        
        error_type = error_details.get('error_type', '')
        
        # Kritik hatalar
        if 'connection_refused' in error_type.lower():
            return IssueSeverity.HIGH
        
        # Sistem kaynak durumuna göre
        cpu_usage = system_context.resource_usage.get('cpu_percent', 0)
        if cpu_usage > 90:
            return IssueSeverity.CRITICAL
        elif cpu_usage > 70:
            return IssueSeverity.HIGH
        
        return IssueSeverity.MEDIUM
    
    def _build_remediation_actions(
        self, 
        solutions: List[Dict[str, Any]], 
        issue_type: str
    ) -> List[RemediationAction]:
        """Çözüm eylemlerini oluşturur"""
        
        actions = []
        
        for i, solution in enumerate(solutions):
            action = RemediationAction(
                action_id=f"{issue_type}_{i}_{datetime.now().timestamp()}",
                title=solution.get('title', f'Solution {i+1}'),
                description=solution.get('description', ''),
                action_type=ActionType(solution.get('action_type', 'manual')),
                risk_level=solution.get('risk_level', 'medium'),
                estimated_duration=solution.get('estimated_time', 'Unknown'),
                requires_approval=solution.get('requires_approval', True),
                steps=solution.get('steps', []),
                automation_script=solution.get('automation_script')
            )
            actions.append(action)
        
        return actions
    
    def _build_performance_remediation_actions(
        self, 
        metrics: Dict[str, float], 
        solutions: List[Dict[str, Any]]
    ) -> List[RemediationAction]:
        """Performans sorunları için çözüm eylemleri"""
        
        actions = self._build_remediation_actions(solutions, 'performance')
        
        # Varsayılan performans çözümleri ekle
        cpu_usage = metrics.get('cpu_percent', 0)
        memory_usage = metrics.get('memory_percent', 0)
        
        if cpu_usage > 80:
            actions.append(RemediationAction(
                action_id=f"cpu_optimization_{datetime.now().timestamp()}",
                title="CPU Kullanımını Optimize Et",
                description="Yüksek CPU kullanımını azaltmak için öneriler",
                action_type=ActionType.AI_ASSISTED,
                risk_level="low",
                estimated_duration="2-5 dakika",
                requires_approval=False,
                steps=[
                    "Yüksek CPU kullanan süreçleri tespit et",
                    "Gereksiz MCP sunucularını yeniden başlat",
                    "Sistem kaynaklarını optimize et"
                ]
            ))
        
        if memory_usage > 85:
            actions.append(RemediationAction(
                action_id=f"memory_cleanup_{datetime.now().timestamp()}",
                title="Bellek Temizliği Yap",
                description="Yüksek bellek kullanımını azalt",
                action_type=ActionType.AUTOMATIC,
                risk_level="safe",
                estimated_duration="1 dakika",
                requires_approval=False,
                steps=[
                    "Bellek cache'ini temizle",
                    "Kullanılmayan süreçleri sonlandır"
                ]
            ))
        
        return actions
    
    def _analyze_performance_trends(
        self, 
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Performans trendlerini analiz eder"""
        
        if not historical_data:
            return {'trend': 'no_data', 'analysis': 'Insufficient historical data'}
        
        # Son 10 veri noktasını al
        recent_data = historical_data[-10:]
        
        # CPU trend analizi
        cpu_values = [d.get('cpu_percent', 0) for d in recent_data]
        cpu_trend = 'stable'
        if len(cpu_values) > 1:
            if cpu_values[-1] > cpu_values[0] * 1.2:
                cpu_trend = 'increasing'
            elif cpu_values[-1] < cpu_values[0] * 0.8:
                cpu_trend = 'decreasing'
        
        # Memory trend analizi
        memory_values = [d.get('memory_percent', 0) for d in recent_data]
        memory_trend = 'stable'
        if len(memory_values) > 1:
            if memory_values[-1] > memory_values[0] * 1.2:
                memory_trend = 'increasing'
            elif memory_values[-1] < memory_values[0] * 0.8:
                memory_trend = 'decreasing'
        
        return {
            'cpu_trend': cpu_trend,
            'memory_trend': memory_trend,
            'data_points': len(recent_data),
            'analysis': f'CPU {cpu_trend}, Memory {memory_trend}'
        }
    
    def _update_pattern_recognition(self, learning_data: LearningData) -> None:
        """Pattern recognition verilerini günceller"""
        
        pattern = learning_data.error_pattern
        
        if pattern not in self.pattern_recognition_data:
            self.pattern_recognition_data[pattern] = {
                'occurrences': 0,
                'success_rate': 0.0,
                'avg_resolution_time': 0.0,
                'user_satisfaction': 0.0
            }
        
        data = self.pattern_recognition_data[pattern]
        data['occurrences'] += 1
        
        if learning_data.solution_effectiveness:
            data['success_rate'] = (
                (data['success_rate'] * (data['occurrences'] - 1) + 
                 learning_data.solution_effectiveness) / data['occurrences']
            )
        
        if learning_data.resolution_time:
            data['avg_resolution_time'] = (
                (data['avg_resolution_time'] * (data['occurrences'] - 1) + 
                 learning_data.resolution_time) / data['occurrences']
            )
        
        if learning_data.user_satisfaction:
            data['user_satisfaction'] = (
                (data['user_satisfaction'] * (data['occurrences'] - 1) + 
                 learning_data.user_satisfaction) / data['occurrences']
            )
    
    # Fallback methods
    
    def _get_fallback_connection_diagnosis(
        self, 
        error_details: Dict[str, Any], 
        system_context: SystemContext
    ) -> DiagnosisResult:
        """AI analizi başarısız olduğunda fallback tanı"""
        
        return DiagnosisResult(
            issue_type="connection_error",
            severity=IssueSeverity.HIGH,
            root_cause_analysis="Backend sunucusuna bağlantı kurulamıyor",
            user_friendly_explanation=self._get_default_connection_explanation(
                error_details.get('error_type', 'unknown')
            ),
            confidence_score=0.6,
            suggested_actions=self._get_default_remediation_actions('connection_error'),
            learning_data={'fallback': True, 'error_details': error_details},
            timestamp=datetime.now()
        )
    
    def _get_fallback_performance_diagnosis(
        self, 
        metrics: Dict[str, float]
    ) -> DiagnosisResult:
        """Performans analizi fallback'i"""
        
        return DiagnosisResult(
            issue_type="performance_issue",
            severity=IssueSeverity.MEDIUM,
            root_cause_analysis="Sistem kaynak kullanımı yüksek",
            user_friendly_explanation=self._get_default_performance_explanation(metrics),
            confidence_score=0.7,
            suggested_actions=self._get_default_remediation_actions('performance_issue'),
            learning_data={'fallback': True, 'metrics': metrics},
            timestamp=datetime.now()
        )
    
    def _get_default_connection_explanation(self, error_type: str) -> str:
        """Varsayılan bağlantı hatası açıklaması"""
        
        explanations = {
            'connection_refused': "Backend sunucusu çalışmıyor veya bağlantıları reddediyor. Sunucunun başlatılması gerekebilir.",
            'timeout': "Sunucu yanıt vermekte gecikiyor. Ağ bağlantısı yavaş olabilir veya sunucu yoğun olabilir.",
            'network_error': "Ağ bağlantısı sorunu var. İnternet bağlantınızı kontrol edin.",
            'unknown': "Bilinmeyen bir bağlantı sorunu oluştu. Sunucu durumunu kontrol edin."
        }
        
        return explanations.get(error_type, explanations['unknown'])
    
    def _get_default_performance_explanation(self, metrics: Dict[str, float]) -> str:
        """Varsayılan performans sorunu açıklaması"""
        
        cpu = metrics.get('cpu_percent', 0)
        memory = metrics.get('memory_percent', 0)
        
        if cpu > 80 and memory > 80:
            return "Sistem hem CPU hem de bellek açısından yoğun çalışıyor. Performans optimizasyonu gerekli."
        elif cpu > 80:
            return f"CPU kullanımı yüksek (%{cpu}). Bazı süreçler çok kaynak tüketiyor olabilir."
        elif memory > 80:
            return f"Bellek kullanımı yüksek (%{memory}). Bellek temizliği gerekebilir."
        else:
            return "Sistem performansında genel bir yavaşlama tespit edildi."
    
    def _get_default_remediation_actions(self, issue_type: str) -> List[RemediationAction]:
        """Varsayılan çözüm eylemleri"""
        
        if issue_type == 'connection_error':
            return [
                RemediationAction(
                    action_id=f"default_connection_1_{datetime.now().timestamp()}",
                    title="Backend Sunucusunu Başlat",
                    description="Backend sunucusunun çalışıp çalışmadığını kontrol edin ve gerekirse başlatın",
                    action_type=ActionType.MANUAL,
                    risk_level="safe",
                    estimated_duration="2 dakika",
                    requires_approval=False,
                    steps=[
                        "Terminal açın",
                        "Backend klasörüne gidin (cd backend)",
                        "python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 komutunu çalıştırın"
                    ]
                ),
                RemediationAction(
                    action_id=f"default_connection_2_{datetime.now().timestamp()}",
                    title="Ağ Bağlantısını Kontrol Et",
                    description="İnternet bağlantınızı ve yerel ağ ayarlarınızı kontrol edin",
                    action_type=ActionType.MANUAL,
                    risk_level="safe",
                    estimated_duration="1 dakika",
                    requires_approval=False,
                    steps=[
                        "İnternet bağlantınızı test edin",
                        "Firewall ayarlarını kontrol edin",
                        "Proxy ayarlarını kontrol edin"
                    ]
                )
            ]
        
        elif issue_type == 'performance_issue':
            return [
                RemediationAction(
                    action_id=f"default_performance_1_{datetime.now().timestamp()}",
                    title="Sistem Kaynaklarını Optimize Et",
                    description="Yüksek kaynak kullanan süreçleri tespit edin ve optimize edin",
                    action_type=ActionType.AI_ASSISTED,
                    risk_level="low",
                    estimated_duration="3 dakika",
                    requires_approval=True,
                    steps=[
                        "Görev yöneticisini açın",
                        "Yüksek CPU/bellek kullanan süreçleri tespit edin",
                        "Gereksiz süreçleri sonlandırın"
                    ]
                )
            ]
        
        return []


    async def record_resolution_outcome(
        self,
        issue_id: str,
        issue_type: str,
        context: Dict[str, Any],
        action_taken: str,
        success: bool,
        resolution_time_seconds: float,
        confidence_score: float = None
    ) -> str:
        """Çözüm sonucunu learning database'e kaydet"""
        try:
            from .ai_learning import get_ai_learning_database, ResolutionOutcome
            
            learning_db = get_ai_learning_database()
            
            outcome = ResolutionOutcome.SUCCESS if success else ResolutionOutcome.FAILURE
            
            event_id = await learning_db.record_issue_resolution(
                issue_id=issue_id,
                issue_type=issue_type,
                context=context,
                action_taken=action_taken,
                outcome=outcome,
                resolution_time_seconds=resolution_time_seconds,
                confidence_score=confidence_score
            )
            
            logger.info(f"Recorded resolution outcome for {issue_id}: {outcome.value}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to record resolution outcome: {e}")
            return ""
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Learning insights'ları getir"""
        try:
            from .ai_learning import get_ai_learning_database
            
            learning_db = get_ai_learning_database()
            insights = await learning_db.get_learning_insights()
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get learning insights: {e}")
            return {}


# Singleton instance
_ai_diagnostics_engine = None


def get_ai_diagnostics_engine() -> AIDiagnosticsEngine:
    """AI Diagnostics Engine singleton"""
    global _ai_diagnostics_engine
    if _ai_diagnostics_engine is None:
        _ai_diagnostics_engine = AIDiagnosticsEngine()
    return _ai_diagnostics_engine