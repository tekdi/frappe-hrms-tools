"""
Audit Logging Service
Logs all CV analysis requests and responses for audit trail
"""
import sqlite3
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AuditLogger:
    """Handles audit logging of CV analysis operations"""

    def __init__(self, db_path: str = "database/audit_logs.db"):
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create audit logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cv_analysis_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT UNIQUE NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    cv_filename TEXT NOT NULL,
                    position_title TEXT,
                    company_name TEXT,
                    llm_provider TEXT NOT NULL,
                    llm_model TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    tokens_used INTEGER,
                    processing_time_ms INTEGER NOT NULL,
                    overall_score REAL,
                    recommendation TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON cv_analysis_logs(timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_id
                ON cv_analysis_logs(analysis_id)
            ''')

            # Create token usage tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    llm_provider TEXT NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    request_count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, llm_provider)
                )
            ''')

            conn.commit()
            logger.info("Audit database initialized")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()

    def log_analysis(
        self,
        analysis_id: str,
        cv_filename: str,
        position_title: str,
        company_name: str,
        llm_provider: str,
        llm_model: str,
        prompt_version: str,
        tokens_used: Optional[int],
        processing_time_ms: int,
        overall_score: Optional[float] = None,
        recommendation: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """
        Log a CV analysis operation

        Args:
            analysis_id: Unique analysis identifier
            cv_filename: Name of the CV file
            position_title: Job position title
            company_name: Company name
            llm_provider: LLM provider used
            llm_model: Specific model used
            prompt_version: Version of prompt used
            tokens_used: Number of tokens consumed
            processing_time_ms: Processing time in milliseconds
            overall_score: Overall candidate score
            recommendation: Hiring recommendation
            status: Status of analysis (success, error, partial)
            error_message: Error message if failed
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO cv_analysis_logs (
                        analysis_id, timestamp, cv_filename, position_title,
                        company_name, llm_provider, llm_model, prompt_version,
                        tokens_used, processing_time_ms, overall_score,
                        recommendation, status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_id,
                    datetime.utcnow(),
                    cv_filename,
                    position_title,
                    company_name,
                    llm_provider,
                    llm_model,
                    prompt_version,
                    tokens_used,
                    processing_time_ms,
                    overall_score,
                    recommendation,
                    status,
                    error_message
                ))

                conn.commit()

                # Update token usage stats
                if tokens_used and status == "success":
                    self._update_token_usage(llm_provider, tokens_used)

                logger.info(f"Logged analysis: {analysis_id} - {status}")

        except sqlite3.IntegrityError as e:
            logger.warning(f"Duplicate analysis_id or constraint violation: {e}")
        except Exception as e:
            logger.error(f"Failed to log analysis: {e}")

    def _update_token_usage(self, llm_provider: str, tokens: int):
        """Update daily token usage statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                today = datetime.utcnow().date()

                # Try to update existing record
                cursor.execute('''
                    INSERT INTO token_usage (date, llm_provider, total_tokens, request_count)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(date, llm_provider)
                    DO UPDATE SET
                        total_tokens = total_tokens + ?,
                        request_count = request_count + 1
                ''', (today, llm_provider, tokens, tokens))

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to update token usage: {e}")

    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis log by ID

        Args:
            analysis_id: Analysis identifier

        Returns:
            Dict with analysis log data or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM cv_analysis_logs WHERE analysis_id = ?',
                    (analysis_id,)
                )
                row = cursor.fetchone()

                if row:
                    return dict(row)
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve analysis: {e}")
            return None

    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent analysis logs

        Args:
            limit: Maximum number of records to return

        Returns:
            List of analysis log dicts
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM cv_analysis_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to retrieve recent analyses: {e}")
            return []

    def get_token_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get token usage statistics

        Args:
            days: Number of days to include

        Returns:
            Dict with usage statistics by provider
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get usage by provider for last N days
                cursor.execute('''
                    SELECT
                        llm_provider,
                        SUM(total_tokens) as total_tokens,
                        SUM(request_count) as total_requests,
                        AVG(total_tokens * 1.0 / request_count) as avg_tokens_per_request
                    FROM token_usage
                    WHERE date >= date('now', '-' || ? || ' days')
                    GROUP BY llm_provider
                ''', (days,))

                stats = {}
                for row in cursor.fetchall():
                    stats[row['llm_provider']] = {
                        'total_tokens': row['total_tokens'],
                        'total_requests': row['total_requests'],
                        'avg_tokens_per_request': round(row['avg_tokens_per_request'], 2)
                    }

                return stats

        except Exception as e:
            logger.error(f"Failed to get token usage stats: {e}")
            return {}


# Global audit logger instance
_audit_logger_instance: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance"""
    global _audit_logger_instance
    if _audit_logger_instance is None:
        _audit_logger_instance = AuditLogger()
    return _audit_logger_instance
