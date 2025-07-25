"""
AI Learning System - Enables AI to learn from past experiences and improve over time

Bu servis, AI'ın geçmiş deneyimlerinden öğrenmesini ve zamanla daha iyi öneriler sunmasını sağlar.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class ResolutionOutcome(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    USER_CANCELLED = "user_cancelled"


class LearningEventType(Enum):
    ISSUE_RESOLUTION = "issue_resolution"
    ACTION_EXECUTION = "action_execution"
    USER_FEEDBACK = "user_feedback"
    PATTERN_DETECTION = "pattern_detection"


@dataclass
class LearningEvent:
    """Öğrenme olayı"""
    id: str
    event_type: LearningEventType
    timestamp: datetime
    issue_type: str
    context: Dict[str, Any]
    action_taken: Optional[str] = None
    outcome: Optional[ResolutionOutcome] = None
    user_feedback: Optional[Dict[str, Any]] = None
    resolution_time_seconds: Optional[float] = None
    confidence_score: Optional[float] = None
    effectiveness_score: Optional[float] = None


@dataclass
class IssuePattern:
    """Sorun pattern'i"""
    pattern_id: str
    issue_type: str
    common_context: Dict[str, Any]
    successful_actions: List[str]
    failed_actions: List[str]
    success_rate: float
    occurrence_count: int
    last_seen: datetime
    confidence: float


@dataclass
class ActionEffectiveness:
    """Eylem etkinliği"""
    action_type: str
    issue_type: str
    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    average_resolution_time: float
    user_satisfaction_avg: float
    success_rate: float
    confidence_interval: Tuple[float, float]


class AILearningDatabase:
    """AI Öğrenme Veritabanı"""
    
    def __init__(self):
        self.learning_events: List[LearningEvent] = []
        self.issue_patterns: Dict[str, IssuePattern] = {}
        self.action_effectiveness: Dict[str, ActionEffectiveness] = {}
        self.user_preferences: Dict[str, Any] = {}
        self.system_insights: List[Dict[str, Any]] = []
        
        # In-memory storage for now - in production, this would be a real database
        self._storage_file = "ai_learning_data.json"
        self._load_data()
    
    def _load_data(self):
        """Veriyi dosyadan yükle"""
        try:
            with open(self._storage_file, 'r') as f:
                data = json.load(f)
                
                # Load learning events
                for event_data in data.get('learning_events', []):
                    event = LearningEvent(
                        id=event_data['id'],
                        event_type=LearningEventType(event_data['event_type']),
                        timestamp=datetime.fromisoformat(event_data['timestamp']),
                        issue_type=event_data['issue_type'],
                        context=event_data['context'],
                        action_taken=event_data.get('action_taken'),
                        outcome=ResolutionOutcome(event_data['outcome']) if event_data.get('outcome') else None,
                        user_feedback=event_data.get('user_feedback'),
                        resolution_time_seconds=event_data.get('resolution_time_seconds'),
                        confidence_score=event_data.get('confidence_score'),
                        effectiveness_score=event_data.get('effectiveness_score')
                    )
                    self.learning_events.append(event)
                
                # Load other data
                self.user_preferences = data.get('user_preferences', {})
                self.system_insights = data.get('system_insights', [])
                
        except FileNotFoundError:
            logger.info("No existing learning data found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load learning data: {e}")
    
    def _save_data(self):
        """Veriyi dosyaya kaydet"""
        try:
            data = {
                'learning_events': [
                    {
                        'id': event.id,
                        'event_type': event.event_type.value,
                        'timestamp': event.timestamp.isoformat(),
                        'issue_type': event.issue_type,
                        'context': event.context,
                        'action_taken': event.action_taken,
                        'outcome': event.outcome.value if event.outcome else None,
                        'user_feedback': event.user_feedback,
                        'resolution_time_seconds': event.resolution_time_seconds,
                        'confidence_score': event.confidence_score,
                        'effectiveness_score': event.effectiveness_score
                    }
                    for event in self.learning_events
                ],
                'user_preferences': self.user_preferences,
                'system_insights': self.system_insights
            }
            
            with open(self._storage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")
    
    async def record_issue_resolution(
        self,
        issue_id: str,
        issue_type: str,
        context: Dict[str, Any],
        action_taken: str,
        outcome: ResolutionOutcome,
        resolution_time_seconds: float,
        confidence_score: float = None
    ) -> str:
        """Sorun çözümünü kaydet"""
        
        event = LearningEvent(
            id=f"resolution_{issue_id}_{datetime.now().timestamp()}",
            event_type=LearningEventType.ISSUE_RESOLUTION,
            timestamp=datetime.now(),
            issue_type=issue_type,
            context=context,
            action_taken=action_taken,
            outcome=outcome,
            resolution_time_seconds=resolution_time_seconds,
            confidence_score=confidence_score
        )
        
        self.learning_events.append(event)
        
        # Update patterns and effectiveness
        await self._update_patterns()
        await self._update_action_effectiveness()
        
        self._save_data()
        
        logger.info(f"Recorded issue resolution: {issue_type} -> {outcome.value}")
        return event.id
    
    async def record_user_feedback(
        self,
        event_id: str,
        user_rating: int,  # 1-5 scale
        user_comment: str = "",
        resolution_helpful: bool = True,
        would_use_again: bool = True
    ) -> bool:
        """Kullanıcı feedback'ini kaydet"""
        
        feedback = {
            'rating': user_rating,
            'comment': user_comment,
            'resolution_helpful': resolution_helpful,
            'would_use_again': would_use_again,
            'timestamp': datetime.now().isoformat()
        }
        
        # Find and update the related event
        for event in self.learning_events:
            if event.id == event_id:
                event.user_feedback = feedback
                event.effectiveness_score = user_rating / 5.0  # Normalize to 0-1
                break
        else:
            # Create new feedback event
            feedback_event = LearningEvent(
                id=f"feedback_{event_id}_{datetime.now().timestamp()}",
                event_type=LearningEventType.USER_FEEDBACK,
                timestamp=datetime.now(),
                issue_type="user_feedback",
                context={'original_event_id': event_id},
                user_feedback=feedback,
                effectiveness_score=user_rating / 5.0
            )
            self.learning_events.append(feedback_event)
        
        # Update user preferences
        await self._update_user_preferences(feedback)
        
        self._save_data()
        
        logger.info(f"Recorded user feedback for event {event_id}: {user_rating}/5")
        return True
    
    async def _update_patterns(self):
        """Pattern'leri güncelle"""
        
        # Group events by issue type
        issue_groups = defaultdict(list)
        for event in self.learning_events:
            if event.event_type == LearningEventType.ISSUE_RESOLUTION:
                issue_groups[event.issue_type].append(event)
        
        # Analyze patterns for each issue type
        for issue_type, events in issue_groups.items():
            if len(events) < 3:  # Need at least 3 events to detect pattern
                continue
            
            # Find common context elements
            context_keys = set()
            for event in events:
                context_keys.update(event.context.keys())
            
            common_context = {}
            for key in context_keys:
                values = [event.context.get(key) for event in events if key in event.context]
                if len(set(values)) == 1:  # All events have same value
                    common_context[key] = values[0]
            
            # Categorize actions by success
            successful_actions = []
            failed_actions = []
            
            for event in events:
                if event.outcome == ResolutionOutcome.SUCCESS:
                    successful_actions.append(event.action_taken)
                elif event.outcome == ResolutionOutcome.FAILURE:
                    failed_actions.append(event.action_taken)
            
            # Calculate success rate
            total_events = len(events)
            successful_events = len([e for e in events if e.outcome == ResolutionOutcome.SUCCESS])
            success_rate = successful_events / total_events if total_events > 0 else 0
            
            # Create or update pattern
            pattern_id = f"pattern_{issue_type}_{hash(str(sorted(common_context.items())))}"
            
            pattern = IssuePattern(
                pattern_id=pattern_id,
                issue_type=issue_type,
                common_context=common_context,
                successful_actions=list(set(successful_actions)),
                failed_actions=list(set(failed_actions)),
                success_rate=success_rate,
                occurrence_count=total_events,
                last_seen=max(event.timestamp for event in events),
                confidence=min(1.0, total_events / 10.0)  # Confidence increases with more data
            )
            
            self.issue_patterns[pattern_id] = pattern
    
    async def _update_action_effectiveness(self):
        """Eylem etkinliğini güncelle"""
        
        # Group by action type and issue type
        action_groups = defaultdict(lambda: defaultdict(list))
        
        for event in self.learning_events:
            if (event.event_type == LearningEventType.ISSUE_RESOLUTION and 
                event.action_taken and event.outcome):
                
                action_groups[event.action_taken][event.issue_type].append(event)
        
        # Calculate effectiveness for each action-issue combination
        for action_type, issue_groups in action_groups.items():
            for issue_type, events in issue_groups.items():
                if len(events) < 2:  # Need at least 2 events for meaningful stats
                    continue
                
                total_attempts = len(events)
                successful_attempts = len([e for e in events if e.outcome == ResolutionOutcome.SUCCESS])
                failed_attempts = len([e for e in events if e.outcome == ResolutionOutcome.FAILURE])
                
                # Calculate average resolution time
                resolution_times = [e.resolution_time_seconds for e in events if e.resolution_time_seconds]
                avg_resolution_time = statistics.mean(resolution_times) if resolution_times else 0
                
                # Calculate user satisfaction
                satisfaction_scores = []
                for event in events:
                    if event.user_feedback and 'rating' in event.user_feedback:
                        satisfaction_scores.append(event.user_feedback['rating'])
                
                avg_satisfaction = statistics.mean(satisfaction_scores) if satisfaction_scores else 3.0
                
                # Calculate success rate and confidence interval
                success_rate = successful_attempts / total_attempts
                
                # Simple confidence interval (binomial proportion)
                if total_attempts > 0:
                    margin_error = 1.96 * (success_rate * (1 - success_rate) / total_attempts) ** 0.5
                    confidence_interval = (
                        max(0, success_rate - margin_error),
                        min(1, success_rate + margin_error)
                    )
                else:
                    confidence_interval = (0, 1)
                
                effectiveness_key = f"{action_type}_{issue_type}"
                
                effectiveness = ActionEffectiveness(
                    action_type=action_type,
                    issue_type=issue_type,
                    total_attempts=total_attempts,
                    successful_attempts=successful_attempts,
                    failed_attempts=failed_attempts,
                    average_resolution_time=avg_resolution_time,
                    user_satisfaction_avg=avg_satisfaction,
                    success_rate=success_rate,
                    confidence_interval=confidence_interval
                )
                
                self.action_effectiveness[effectiveness_key] = effectiveness
    
    async def _update_user_preferences(self, feedback: Dict[str, Any]):
        """Kullanıcı tercihlerini güncelle"""
        
        # Track user preferences based on feedback
        if 'rating' in feedback:
            if 'rating_history' not in self.user_preferences:
                self.user_preferences['rating_history'] = []
            
            self.user_preferences['rating_history'].append({
                'rating': feedback['rating'],
                'timestamp': feedback['timestamp']
            })
            
            # Keep only last 100 ratings
            self.user_preferences['rating_history'] = self.user_preferences['rating_history'][-100:]
        
        # Update average satisfaction
        ratings = [r['rating'] for r in self.user_preferences.get('rating_history', [])]
        if ratings:
            self.user_preferences['average_satisfaction'] = statistics.mean(ratings)
            self.user_preferences['satisfaction_trend'] = self._calculate_trend(ratings)
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Trend hesapla"""
        if len(values) < 5:
            return "insufficient_data"
        
        recent = values[-5:]
        older = values[-10:-5] if len(values) >= 10 else values[:-5]
        
        if not older:
            return "insufficient_data"
        
        recent_avg = statistics.mean(recent)
        older_avg = statistics.mean(older)
        
        if recent_avg > older_avg + 0.2:
            return "improving"
        elif recent_avg < older_avg - 0.2:
            return "declining"
        else:
            return "stable"
    
    async def get_recommendations_for_issue(
        self,
        issue_type: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Sorun için öneriler getir"""
        
        recommendations = []
        
        # Find matching patterns
        matching_patterns = []
        for pattern in self.issue_patterns.values():
            if pattern.issue_type == issue_type:
                # Check context similarity
                similarity_score = self._calculate_context_similarity(
                    pattern.common_context, context
                )
                if similarity_score > 0.5:  # At least 50% similarity
                    matching_patterns.append((pattern, similarity_score))
        
        # Sort by similarity and success rate
        matching_patterns.sort(key=lambda x: (x[1], x[0].success_rate), reverse=True)
        
        # Generate recommendations from patterns
        for pattern, similarity in matching_patterns[:3]:  # Top 3 patterns
            for action in pattern.successful_actions:
                effectiveness_key = f"{action}_{issue_type}"
                effectiveness = self.action_effectiveness.get(effectiveness_key)
                
                recommendation = {
                    'action': action,
                    'confidence': pattern.confidence * similarity,
                    'success_rate': pattern.success_rate,
                    'pattern_match': similarity,
                    'historical_occurrences': pattern.occurrence_count,
                    'last_successful': pattern.last_seen.isoformat(),
                    'effectiveness': effectiveness.success_rate if effectiveness else None,
                    'avg_resolution_time': effectiveness.average_resolution_time if effectiveness else None,
                    'user_satisfaction': effectiveness.user_satisfaction_avg if effectiveness else None
                }
                
                recommendations.append(recommendation)
        
        # Sort by overall score
        for rec in recommendations:
            score = (
                rec['confidence'] * 0.3 +
                rec['success_rate'] * 0.4 +
                rec['pattern_match'] * 0.3
            )
            rec['overall_score'] = score
        
        recommendations.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _calculate_context_similarity(
        self,
        pattern_context: Dict[str, Any],
        current_context: Dict[str, Any]
    ) -> float:
        """Context benzerliği hesapla"""
        
        if not pattern_context:
            return 0.0
        
        matching_keys = 0
        total_keys = len(pattern_context)
        
        for key, value in pattern_context.items():
            if key in current_context and current_context[key] == value:
                matching_keys += 1
        
        return matching_keys / total_keys if total_keys > 0 else 0.0
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Öğrenme insights'ları getir"""
        
        total_events = len(self.learning_events)
        resolution_events = [e for e in self.learning_events if e.event_type == LearningEventType.ISSUE_RESOLUTION]
        
        if not resolution_events:
            return {
                'total_events': total_events,
                'insights': [],
                'message': 'Insufficient data for insights'
            }
        
        # Success rate over time
        successful_resolutions = len([e for e in resolution_events if e.outcome == ResolutionOutcome.SUCCESS])
        overall_success_rate = successful_resolutions / len(resolution_events)
        
        # Most common issues
        issue_counts = Counter(e.issue_type for e in resolution_events)
        most_common_issues = issue_counts.most_common(5)
        
        # Best performing actions
        action_performance = []
        for effectiveness in self.action_effectiveness.values():
            if effectiveness.total_attempts >= 3:  # Only include actions with enough data
                action_performance.append({
                    'action': effectiveness.action_type,
                    'issue_type': effectiveness.issue_type,
                    'success_rate': effectiveness.success_rate,
                    'attempts': effectiveness.total_attempts,
                    'user_satisfaction': effectiveness.user_satisfaction_avg
                })
        
        action_performance.sort(key=lambda x: x['success_rate'], reverse=True)
        
        # User satisfaction trend
        satisfaction_trend = self.user_preferences.get('satisfaction_trend', 'unknown')
        avg_satisfaction = self.user_preferences.get('average_satisfaction', 0)
        
        insights = {
            'total_events': total_events,
            'total_resolutions': len(resolution_events),
            'overall_success_rate': overall_success_rate,
            'most_common_issues': most_common_issues,
            'best_performing_actions': action_performance[:5],
            'user_satisfaction': {
                'average': avg_satisfaction,
                'trend': satisfaction_trend
            },
            'patterns_discovered': len(self.issue_patterns),
            'learning_maturity': min(1.0, total_events / 100.0),  # 0-1 scale
            'recommendations_available': len(self.action_effectiveness) > 0
        }
        
        return insights
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Eski verileri temizle"""
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Remove old events
        self.learning_events = [
            event for event in self.learning_events
            if event.timestamp > cutoff_date
        ]
        
        # Update patterns and effectiveness after cleanup
        await self._update_patterns()
        await self._update_action_effectiveness()
        
        self._save_data()
        
        logger.info(f"Cleaned up learning data older than {days_to_keep} days")


# Singleton instance
_ai_learning_db = None


def get_ai_learning_database() -> AILearningDatabase:
    """AI Learning Database singleton"""
    global _ai_learning_db
    if _ai_learning_db is None:
        _ai_learning_db = AILearningDatabase()
    return _ai_learning_db