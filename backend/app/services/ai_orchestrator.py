"""
AI Action Orchestrator - Orchestrates the complete AI decision-making cycle

Bu servis, AI'ın Issue detection → Analysis → Suggestion → Action → Validation 
döngüsünün tamamını yönetir ve koordine eder.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .ai_diagnostics import get_ai_diagnostics_engine
from .security_manager import get_security_manager, RiskLevel
from .health_monitor import get_health_monitor
from .proactive_monitor import get_proactive_monitor

logger = logging.getLogger(__name__)


class ActionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionType(Enum):
    MCP_SERVER_RESTART = "mcp_server_restart"
    SYSTEM_CLEANUP = "system_cleanup"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    DIAGNOSTIC_ANALYSIS = "diagnostic_analysis"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ActionRequest:
    """AI eylem talebi"""
    id: str
    action_type: ActionType
    title: str
    description: str
    parameters: Dict[str, Any]
    risk_level: RiskLevel
    estimated_duration: str
    requires_approval: bool
    created_at: datetime
    diagnosis_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class ActionExecution:
    """Eylem yürütme durumu"""
    request_id: str
    status: ActionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None


class AIActionOrchestrator:
    """AI Eylem Orkestratörü"""
    
    def __init__(self):
        self.pending_actions: Dict[str, ActionRequest] = {}
        self.active_executions: Dict[str, ActionExecution] = {}
        self.completed_actions: List[ActionExecution] = []
        self.orchestration_active = False
        
    async def start_orchestration(self):
        """Orkestrasyon sürecini başlat"""
        if self.orchestration_active:
            return
            
        self.orchestration_active = True
        logger.info("AI Action Orchestrator started")
        
        # Orchestration loop'unu başlat
        asyncio.create_task(self._orchestration_loop())
    
    async def stop_orchestration(self):
        """Orkestrasyon sürecini durdur"""
        self.orchestration_active = False
        logger.info("AI Action Orchestrator stopped")
    
    async def _orchestration_loop(self):
        """Ana orkestrasyon döngüsü"""
        while self.orchestration_active:
            try:
                # 1. Issue Detection
                await self._detect_issues()
                
                # 2. Process Pending Actions
                await self._process_pending_actions()
                
                # 3. Monitor Active Executions
                await self._monitor_executions()
                
                # 4. Validate Completed Actions
                await self._validate_completed_actions()
                
                await asyncio.sleep(60)  # Her dakika kontrol et
                
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                await asyncio.sleep(60)
    
    async def _detect_issues(self):
        """Sorun tespit etme"""
        try:
            # Proactive monitor'dan AI insights al
            proactive_monitor = get_proactive_monitor()
            insights = await proactive_monitor.get_ai_insights()
            
            for insight in insights:
                # Yüksek öncelikli sorunlar için otomatik eylem öner
                severity_check = insight.get('severity') in ['error', 'critical']
                confidence_check = insight.get('confidence', 0) > 0.7
                if severity_check and confidence_check:
                    
                    await self._create_action_from_insight(insight)
                    
        except Exception as e:
            logger.error(f"Issue detection failed: {e}")
    
    async def _create_action_from_insight(self, insight: Dict[str, Any]):
        """AI insight'tan eylem oluştur"""
        try:
            # Insight'tan eylem türünü belirle
            action_type = self._determine_action_type(insight)
            
            if not action_type:
                return
            
            # Eylem parametrelerini hazırla
            parameters = self._build_action_parameters(insight, action_type)
            
            # Risk seviyesini belirle
            risk_level = self._determine_risk_level(insight, action_type)
            
            # Eylem talebi oluştur
            action_request = ActionRequest(
                id=str(uuid.uuid4()),
                action_type=action_type,
                title=f"AI Suggested: {insight.get('title', 'System Action')}",
                description=insight.get('message', ''),
                parameters=parameters,
                risk_level=risk_level,
                estimated_duration=self._estimate_duration(action_type),
                requires_approval=risk_level in [
                    RiskLevel.HIGH, RiskLevel.CRITICAL
                ],
                created_at=datetime.now(),
                diagnosis_id=insight.get('id')
            )
            
            # Güvenlik kontrolü
            security_manager = get_security_manager()
            can_perform, reason, _ = (
                security_manager.can_ai_perform_operation(
                    action_type.value, parameters
                )
            )
            
            if can_perform or action_request.requires_approval:
                self.pending_actions[action_request.id] = action_request
                logger.info(f"AI Action created: {action_request.title}")
            else:
                logger.warning(f"AI Action blocked: {reason}")
                
        except Exception as e:
            logger.error(f"Failed to create action from insight: {e}")    

    async def _process_pending_actions(self):
        """Bekleyen eylemleri işle"""
        try:
            for action_id, action_request in list(self.pending_actions.items()):
                # Onay gerektiren eylemler için kullanıcı onayını bekle
                if action_request.requires_approval:
                    # TODO: Frontend'e bildirim gönder
                    continue
                
                # Otomatik eylemleri başlat
                await self._execute_action(action_request)
                
        except Exception as e:
            logger.error(f"Failed to process pending actions: {e}")
    
    async def _execute_action(self, action_request: ActionRequest):
        """Eylemi yürüt"""
        execution = ActionExecution(
            request_id=action_request.id,
            status=ActionStatus.EXECUTING,
            started_at=datetime.now()
        )
        
        try:
            self.active_executions[action_request.id] = execution
            
            # Pending'den kaldır
            if action_request.id in self.pending_actions:
                del self.pending_actions[action_request.id]
            
            logger.info(f"Executing AI Action: {action_request.title}")
            
            # Eylem türüne göre yürütme
            result = await self._execute_by_type(action_request)
            
            # Sonucu kaydet
            execution.status = ActionStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.result = result
            
            logger.info(f"AI Action completed: {action_request.title}")
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            execution.status = ActionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
    
    async def _execute_by_type(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Eylem türüne göre yürütme"""
        
        if action_request.action_type == ActionType.MCP_SERVER_RESTART:
            return await self._execute_mcp_restart(action_request)
        
        elif action_request.action_type == ActionType.SYSTEM_CLEANUP:
            return await self._execute_system_cleanup(action_request)
        
        elif action_request.action_type == ActionType.PERFORMANCE_OPTIMIZATION:
            return await self._execute_performance_optimization(action_request)
        
        elif action_request.action_type == ActionType.DIAGNOSTIC_ANALYSIS:
            return await self._execute_diagnostic_analysis(action_request)
        
        else:
            raise ValueError(f"Unknown action type: {action_request.action_type}")
    
    async def _execute_mcp_restart(self, action_request: ActionRequest) -> Dict[str, Any]:
        """MCP sunucu yeniden başlatma"""
        server_name = action_request.parameters.get('server_name')
        if not server_name:
            raise ValueError("Server name not specified")
        
        health_monitor = get_health_monitor()
        success = await health_monitor.force_restart_server(server_name)
        
        if not success:
            raise RuntimeError(f"Failed to restart server: {server_name}")
        
        return {
            'action': 'mcp_server_restart',
            'server_name': server_name,
            'success': True,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _execute_system_cleanup(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Sistem temizliği"""
        cleanup_type = action_request.parameters.get('cleanup_type', 'memory')
        
        if cleanup_type == 'memory':
            # Memory cleanup simulation
            import gc
            gc.collect()
            
            return {
                'action': 'system_cleanup',
                'cleanup_type': 'memory',
                'success': True,
                'details': 'Memory garbage collection performed'
            }
        
        return {'action': 'system_cleanup', 'success': False, 'reason': 'Unknown cleanup type'}
    
    async def _execute_performance_optimization(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Performans optimizasyonu"""
        optimization_type = action_request.parameters.get('optimization_type', 'general')
        
        # Simulated performance optimization
        return {
            'action': 'performance_optimization',
            'optimization_type': optimization_type,
            'success': True,
            'details': 'Performance optimization completed'
        }
    
    async def _execute_diagnostic_analysis(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Tanı analizi"""
        analysis_type = action_request.parameters.get('analysis_type', 'system_health')
        
        # AI diagnostics engine ile analiz
        ai_engine = get_ai_diagnostics_engine()
        
        # Sistem durumu analizi
        health_monitor = get_health_monitor()
        mcp_statuses = await health_monitor.get_all_statuses()
        
        # Performance metrics al
        import psutil
        metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent
        }
        
        diagnosis = await ai_engine.analyze_performance_issue(metrics, [])
        
        return {
            'action': 'diagnostic_analysis',
            'analysis_type': analysis_type,
            'success': True,
            'diagnosis': {
                'issue_type': diagnosis.issue_type,
                'severity': diagnosis.severity.value,
                'confidence': diagnosis.confidence_score,
                'explanation': diagnosis.user_friendly_explanation,
                'suggestions': len(diagnosis.suggested_actions)
            }
        }
    
    async def _monitor_executions(self):
        """Aktif yürütmeleri izle"""
        try:
            for execution_id, execution in list(self.active_executions.items()):
                # Timeout kontrolü
                if (execution.started_at and
                    datetime.now() - execution.started_at >
                        timedelta(minutes=10)):
                    
                    execution.status = ActionStatus.FAILED
                    execution.error_message = "Execution timeout"
                    execution.completed_at = datetime.now()
                    
                    logger.warning(f"Action execution timed out: {execution_id}")
                
                # Tamamlanan yürütmeleri completed listesine taşı
                completed_statuses = [
                    ActionStatus.COMPLETED, ActionStatus.FAILED,
                    ActionStatus.CANCELLED
                ]
                if execution.status in completed_statuses:
                    self.completed_actions.append(execution)
                    del self.active_executions[execution_id]
                    
        except Exception as e:
            logger.error(f"Failed to monitor executions: {e}")
    
    async def _validate_completed_actions(self):
        """Tamamlanan eylemleri doğrula"""
        try:
            for execution in self.completed_actions[-5:]:  # Son 5 eylemi kontrol et
                if execution.validation_result is None:
                    validation_result = await self._validate_action_result(execution)
                    execution.validation_result = validation_result
                    
        except Exception as e:
            logger.error(f"Failed to validate completed actions: {e}")
    
    async def _validate_action_result(self, execution: ActionExecution) -> Dict[str, Any]:
        """Eylem sonucunu doğrula"""
        try:
            if execution.status != ActionStatus.COMPLETED:
                return {
                    'validated': False,
                    'reason': 'Action not completed successfully'
                }
            
            # Eylem türüne göre doğrulama
            action_request = None
            for req in [*self.pending_actions.values()]:
                if req.id == execution.request_id:
                    action_request = req
                    break
            
            if not action_request:
                return {
                    'validated': False,
                    'reason': 'Original action request not found'
                }
            
            # MCP restart doğrulaması
            if action_request.action_type == ActionType.MCP_SERVER_RESTART:
                server_name = action_request.parameters.get('server_name')
                if server_name:
                    health_monitor = get_health_monitor()
                    status = await health_monitor.get_server_status(server_name)
                    
                    is_healthy = (status.status.value == 'HEALTHY' 
                                  if hasattr(status.status, 'value') 
                                  else status.status == 'HEALTHY')
                    
                    return {
                        'validated': is_healthy,
                        'server_name': server_name,
                        'current_status': status.status,
                        'validation_time': datetime.now().isoformat()
                    }
            
            # Genel doğrulama
            return {
                'validated': True,
                'reason': 'Action completed successfully',
                'validation_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Action validation failed: {e}")
            return {'validated': False, 'reason': f'Validation error: {str(e)}'}
    
    # Helper methods
    
    def _determine_action_type(self, insight: Dict[str, Any]) -> Optional[ActionType]:
        """Insight'tan eylem türünü belirle"""
        
        # Server-specific issues
        if insight.get('server_name'):
            return ActionType.MCP_SERVER_RESTART
        
        # Performance issues
        message = insight.get('message', '').lower()
        if 'cpu' in message or 'memory' in message:
            return ActionType.PERFORMANCE_OPTIMIZATION

        # Pattern-based issues
        if insight.get('type') == 'pattern_insight':
            return ActionType.DIAGNOSTIC_ANALYSIS

        return None
    
    def _build_action_parameters(self, insight: Dict[str, Any], action_type: ActionType) -> Dict[str, Any]:
        """Eylem parametrelerini oluştur"""
        
        if action_type == ActionType.MCP_SERVER_RESTART:
            return {'server_name': insight.get('server_name')}
        
        elif action_type == ActionType.PERFORMANCE_OPTIMIZATION:
            if 'cpu' in insight.get('message', '').lower():
                return {'optimization_type': 'cpu'}
            elif 'memory' in insight.get('message', '').lower():
                return {'optimization_type': 'memory'}
            return {'optimization_type': 'general'}
        
        elif action_type == ActionType.DIAGNOSTIC_ANALYSIS:
            return {'analysis_type': insight.get('pattern_type', 'system_health')}
        
        return {}
    
    def _determine_risk_level(self, insight: Dict[str, Any], action_type: ActionType) -> RiskLevel:
        """Risk seviyesini belirle"""
        
        # Server restart her zaman yüksek risk
        if action_type == ActionType.MCP_SERVER_RESTART:
            return RiskLevel.HIGH
        
        # Severity'ye göre risk belirleme
        severity = insight.get('severity', 'info')
        if severity == 'critical':
            return RiskLevel.CRITICAL
        elif severity == 'error':
            return RiskLevel.HIGH
        elif severity == 'warning':
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _estimate_duration(self, action_type: ActionType) -> str:
        """Tahmini süre"""
        duration_map = {
            ActionType.MCP_SERVER_RESTART: "30 seconds",
            ActionType.SYSTEM_CLEANUP: "1 minute",
            ActionType.PERFORMANCE_OPTIMIZATION: "2 minutes",
            ActionType.DIAGNOSTIC_ANALYSIS: "1 minute",
            ActionType.MANUAL_INTERVENTION: "Variable"
        }
        return duration_map.get(action_type, "Unknown")
    
    # Public API
    
    async def approve_action(self, action_id: str, user_id: str = "system") -> bool:
        """Eylemi onayla"""
        try:
            if action_id not in self.pending_actions:
                return False
            
            action_request = self.pending_actions[action_id]
            action_request.user_id = user_id
            
            # Eylemi yürüt
            await self._execute_action(action_request)
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve action {action_id}: {e}")
            return False
    
    async def reject_action(self, action_id: str, reason: str = "") -> bool:
        """Eylemi reddet"""
        try:
            if action_id not in self.pending_actions:
                return False
            
            del self.pending_actions[action_id]
            logger.info(f"Action rejected: {action_id} - {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reject action {action_id}: {e}")
            return False
    
    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Bekleyen eylemleri getir"""
        return [
            {
                'id': action.id,
                'title': action.title,
                'description': action.description,
                'action_type': action.action_type.value,
                'risk_level': action.risk_level.value,
                'estimated_duration': action.estimated_duration,
                'created_at': action.created_at.isoformat(),
                'parameters': action.parameters
            }
            for action in self.pending_actions.values()
        ]
    
    def get_action_status(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Eylem durumunu getir"""
        
        # Pending actions
        if action_id in self.pending_actions:
            action = self.pending_actions[action_id]
            return {
                'id': action.id,
                'status': 'pending',
                'title': action.title,
                'created_at': action.created_at.isoformat()
            }
        
        # Active executions
        if action_id in self.active_executions:
            execution = self.active_executions[action_id]
            return {
                'id': action_id,
                'status': execution.status.value,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'result': execution.result
            }
        
        # Completed actions
        for execution in self.completed_actions:
            if execution.request_id == action_id:
                return {
                    'id': action_id,
                    'status': execution.status.value,
                    'started_at': execution.started_at.isoformat() if execution.started_at else None,
                    'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                    'result': execution.result,
                    'validation': execution.validation_result
                }
        
        return None


# Singleton instance
_ai_orchestrator = None


def get_ai_orchestrator() -> AIActionOrchestrator:
    """AI Action Orchestrator singleton"""
    global _ai_orchestrator
    if _ai_orchestrator is None:
        _ai_orchestrator = AIActionOrchestrator()
    return _ai_orchestrator    

    async def _record_learning_outcome(
        self,
        action_id: str,
        issue_type: str,
        context: Dict[str, Any],
        action_taken: str,
        success: bool,
        resolution_time_seconds: float
    ):
        """Learning database'e sonucu kaydet"""
        try:
            from .ai_learning import get_ai_learning_database, ResolutionOutcome
            
            learning_db = get_ai_learning_database()
            
            outcome = ResolutionOutcome.SUCCESS if success else ResolutionOutcome.FAILURE
            
            await learning_db.record_issue_resolution(
                issue_id=action_id,
                issue_type=issue_type,
                context=context,
                action_taken=action_taken,
                outcome=outcome,
                resolution_time_seconds=resolution_time_seconds
            )
            
            logger.info(f"Recorded learning outcome for action {action_id}")
            
        except Exception as e:
            logger.error(f"Failed to record learning outcome: {e}")
    
    async def record_user_feedback(
        self,
        action_id: str,
        user_rating: int,
        user_comment: str = "",
        resolution_helpful: bool = True
    ) -> bool:
        """Kullanıcı feedback'ini kaydet"""
        try:
            from .ai_learning import get_ai_learning_database
            
            learning_db = get_ai_learning_database()
            
            # Find the corresponding learning event
            event_id = f"resolution_{action_id}"
            
            success = await learning_db.record_user_feedback(
                event_id=event_id,
                user_rating=user_rating,
                user_comment=user_comment,
                resolution_helpful=resolution_helpful,
                would_use_again=user_rating >= 4
            )
            
            logger.info(f"Recorded user feedback for action {action_id}: {user_rating}/5")
            return success
            
        except Exception as e:
            logger.error(f"Failed to record user feedback: {e}")
            return False