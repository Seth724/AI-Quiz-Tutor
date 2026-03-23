from __future__ import annotations

import json
import math
import re
import smtplib
import ssl
import uuid
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

from groq import Groq
from pymongo import DESCENDING
from pymongo.database import Database

from config import settings
from services.document_service import document_service


class PersonalizedChatbotService:
    """Memory-enabled chatbot that can answer general and user-data questions."""

    def __init__(
        self,
        db: Database,
        main_collection: str,
        attempts_collection_name: str,
        documents_collection_name: str,
        message_collection_name: str = "assistant_messages",
        profile_collection_name: str = "assistant_profiles",
        study_plan_collection_name: str = "study_plans",
    ) -> None:
        self.db = db
        self.main_collection = main_collection
        self.attempts_collection = db[attempts_collection_name]
        self.documents_collection = db[documents_collection_name]
        self.messages_collection = db[message_collection_name]
        self.profile_collection = db[profile_collection_name]
        self.study_plan_collection = db[study_plan_collection_name]
        self.llm = Groq(api_key=settings.GROQ_API_KEY)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) > 2]

    @staticmethod
    def _dedupe_chunks(chunks: List[Dict[str, Any]], max_items: int) -> List[Dict[str, Any]]:
        seen = set()
        output: List[Dict[str, Any]] = []

        for chunk in chunks:
            text = (chunk.get("text") or "").strip()
            if not text:
                continue

            key = text[:220].lower()
            if key in seen:
                continue

            seen.add(key)
            output.append(chunk)

            if len(output) >= max_items:
                break

        return output

    def _rank_chunks(self, chunks: List[Dict[str, Any]], query: str, max_items: int) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query)
        scored: List[Dict[str, Any]] = []

        for chunk in chunks:
            text = (chunk.get("text") or "").strip()
            if not text:
                continue

            lowered = text.lower()
            overlap = 0
            if query_tokens:
                overlap = sum(1 for token in query_tokens if token in lowered)

            lexical_score = overlap / max(len(query_tokens), 1) if query_tokens else 0.0
            semantic_score = float(chunk.get("score", 0.0) or 0.0)
            score = max(lexical_score, semantic_score)

            scored.append(
                {
                    "text": text,
                    "metadata": chunk.get("metadata", {}) or {},
                    "score": score,
                }
            )

        scored.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
        return self._dedupe_chunks(scored, max_items=max_items)

    def _build_context_from_chunks(self, chunks: List[Dict[str, Any]], max_chars: int = 9000) -> str:
        parts: List[str] = []
        total = 0

        for chunk in chunks:
            text = (chunk.get("text") or "").strip()
            if not text:
                continue

            remaining = max_chars - total
            if remaining <= 0:
                break

            snippet = text if len(text) <= remaining else text[:remaining]
            parts.append(snippet)
            total += len(snippet)

        return "\n\n".join(parts)

    def _extract_name(self, message: str) -> Optional[str]:
        patterns = [
            r"\bmy name is\s+([a-zA-Z][a-zA-Z\s\-']{0,40})",
            r"\bcall me\s+([a-zA-Z][a-zA-Z\s\-']{0,40})",
            r"\bi am\s+([a-zA-Z][a-zA-Z\s\-']{0,40})",
        ]

        for pattern in patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE)
            if not match:
                continue

            raw_name = match.group(1).strip()
            raw_name = re.split(r"[,.!?]", raw_name)[0].strip()
            words = [w for w in raw_name.split() if w]
            if not words or len(words) > 4:
                continue

            normalized = " ".join(word.capitalize() for word in words)
            if len(normalized) < 2:
                continue

            return normalized

        return None

    def _is_name_recall_question(self, message: str) -> bool:
        lowered = (message or "").lower()
        checks = [
            "what is my name",
            "do you remember my name",
            "tell my name",
            "say my name",
            "my name?",
        ]
        return any(check in lowered for check in checks)

    def _is_progress_question(self, message: str) -> bool:
        lowered = (message or "").lower()
        checks = [
            "progress",
            "average score",
            "weak area",
            "weak topic",
            "how am i doing",
            "how i am doing",
            "trend",
            "performance",
            "accuracy",
            "my scores",
        ]
        return any(check in lowered for check in checks)

    def _get_profile(self, user_id: str) -> Dict[str, Any]:
        profile = self.profile_collection.find_one({"_id": user_id})
        return profile or {"_id": user_id, "user_id": user_id}

    def _update_profile_memory(self, user_id: str, message: str) -> Dict[str, Any]:
        profile = self._get_profile(user_id)
        updates: Dict[str, Any] = {"last_seen_at": datetime.utcnow()}

        extracted_name = self._extract_name(message)
        if extracted_name:
            updates["name"] = extracted_name

        self.profile_collection.update_one(
            {"_id": user_id},
            {
                "$set": updates,
                "$setOnInsert": {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                },
            },
            upsert=True,
        )

        profile.update(updates)
        return profile

    def _get_learning_snapshot(self, user_id: str) -> Dict[str, Any]:
        attempts = list(self.attempts_collection.find({"user_id": user_id}).sort("completed_at", DESCENDING).limit(200))
        docs = list(self.documents_collection.find({"user_id": user_id}).sort("created_at", DESCENDING).limit(20))

        avg_score = sum(float(a.get("score", 0.0)) for a in attempts) / len(attempts) if attempts else 0.0

        topic_stats: Dict[str, Dict[str, float]] = {}
        for attempt in attempts:
            for area in attempt.get("weak_areas", []) or []:
                topic = (area.get("topic") or "General").strip() or "General"
                accuracy = float(area.get("accuracy", 0.0) or 0.0)
                if topic not in topic_stats:
                    topic_stats[topic] = {"sum": 0.0, "count": 0.0}
                topic_stats[topic]["sum"] += accuracy
                topic_stats[topic]["count"] += 1

        weak_areas: List[Dict[str, Any]] = []
        for topic, stats in topic_stats.items():
            weak_areas.append(
                {
                    "topic": topic,
                    "accuracy": stats["sum"] / max(stats["count"], 1.0),
                    "attempts": int(stats["count"]),
                }
            )

        weak_areas.sort(key=lambda item: float(item.get("accuracy", 0.0)))

        return {
            "quizzes_completed": len(attempts),
            "average_score": avg_score,
            "weak_areas": weak_areas[:10],
            "documents_count": len(docs),
            "recent_documents": [doc.get("title", "Untitled") for doc in docs[:5]],
        }

    def _build_progress_reply(self, profile: Dict[str, Any], snapshot: Dict[str, Any]) -> str:
        completed = int(snapshot.get("quizzes_completed", 0))
        avg_score = float(snapshot.get("average_score", 0.0)) * 100
        weak_areas = snapshot.get("weak_areas", []) or []
        name = profile.get("name")

        prefix = f"{name}, " if name else ""

        if completed == 0:
            return (
                f"{prefix}you have not completed a quiz yet. Upload a document and take your first quiz. "
                "After that I can track trend, weak areas, and weekly improvement."
            )

        weak_text = "No major weak topics detected right now."
        if weak_areas:
            weak_text = "Top weak areas: " + ", ".join(
                [
                    f"{area.get('topic', 'General')} ({float(area.get('accuracy', 0.0)) * 100:.0f}% accuracy)"
                    for area in weak_areas[:3]
                ]
            )

        return (
            f"{prefix}you have completed {completed} quizzes with an average score of {avg_score:.1f}%. "
            f"{weak_text}"
        )

    def _get_recent_history(self, user_id: str, document_id: Optional[str], limit: int = 12) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"user_id": user_id}
        if document_id:
            query["document_id"] = document_id

        rows = list(self.messages_collection.find(query).sort("created_at", DESCENDING).limit(limit))
        rows.reverse()
        return rows

    def _format_recent_history(self, history: List[Dict[str, Any]]) -> str:
        lines: List[str] = []
        for item in history:
            role = item.get("role", "assistant")
            content = (item.get("content") or "").strip()
            if not content:
                continue
            lines.append(f"{role.upper()}: {content}")
        return "\n".join(lines)

    def _fetch_document_context(self, query: str, document_id: Optional[str], limit: int = 8) -> List[Dict[str, Any]]:
        if not document_id:
            return []

        vector_hits = document_service.search_documents(
            query=query,
            collection_name=self.main_collection,
            limit=limit,
            document_id=document_id,
        )

        ranked = self._rank_chunks(vector_hits, query=query, max_items=limit)

        if len(ranked) < min(limit, 3):
            fallback_hits = document_service.get_document_chunks(
                document_id=document_id,
                collection_name=self.main_collection,
                limit=800,
            )
            combined = ranked + self._rank_chunks(fallback_hits, query=query, max_items=max(10, limit))
            combined.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
            ranked = self._dedupe_chunks(combined, max_items=limit)

        return ranked

    def _store_message(
        self,
        user_id: str,
        role: str,
        content: str,
        document_id: Optional[str],
        confidence: Optional[float] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.messages_collection.insert_one(
            {
                "_id": str(uuid.uuid4()),
                "user_id": user_id,
                "document_id": document_id,
                "role": role,
                "content": content,
                "confidence": confidence,
                "sources": sources or [],
                "created_at": datetime.utcnow(),
            }
        )

    def _build_system_prompt(
        self,
        profile: Dict[str, Any],
        snapshot: Dict[str, Any],
        document_title: Optional[str],
    ) -> str:
        known_name = profile.get("name")
        weak_areas = snapshot.get("weak_areas", []) or []
        weak_area_text = ", ".join([item.get("topic", "General") for item in weak_areas[:5]]) or "none"

        return (
            "You are an AI Study Coach for Quiz Tutor.\n"
            "You can answer general knowledge questions and study questions.\n"
            "When user progress data is available, personalize suggestions using that data.\n"
            "If the user asks what their name is and known name exists, answer exactly with that name.\n"
            "Be concise but educational, and include action steps when useful.\n"
            f"Known user name: {known_name or 'unknown'}\n"
            f"Average score: {float(snapshot.get('average_score', 0.0)) * 100:.1f}%\n"
            f"Weak areas: {weak_area_text}\n"
            f"Selected document: {document_title or 'none'}\n"
        )

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.llm.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.35,
                max_tokens=700,
            )
            content = response.choices[0].message.content if response and response.choices else None
            return (content or "I could not generate a response right now.").strip()
        except Exception:
            return "I am having trouble responding right now. Please try again in a moment."

    def chat(self, user_id: str, message: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        cleaned = (message or "").strip()
        if not cleaned:
            raise ValueError("Message cannot be empty")

        profile = self._update_profile_memory(user_id, cleaned)
        snapshot = self._get_learning_snapshot(user_id)
        document_info = self.documents_collection.find_one({"_id": document_id}) if document_id else None

        self._store_message(user_id=user_id, role="user", content=cleaned, document_id=document_id)

        if self._is_name_recall_question(cleaned) and profile.get("name"):
            reply = f"Your name is {profile['name']}."
            confidence = 0.98
            sources: List[Dict[str, Any]] = []
        elif self._is_progress_question(cleaned) and not document_id:
            reply = self._build_progress_reply(profile, snapshot)
            confidence = 0.9
            sources = [
                {
                    "text": (
                        f"Quizzes completed: {snapshot.get('quizzes_completed', 0)}, "
                        f"Average score: {float(snapshot.get('average_score', 0.0)) * 100:.1f}%"
                    ),
                    "score": 0.9,
                }
            ]
        else:
            chunks = self._fetch_document_context(cleaned, document_id=document_id, limit=8)
            context = self._build_context_from_chunks(chunks, max_chars=9000)
            history = self._get_recent_history(user_id=user_id, document_id=document_id, limit=12)
            history_block = self._format_recent_history(history)
            profile_block = f"Known user name: {profile.get('name', 'unknown')}"
            progress_block = (
                f"Quizzes completed: {snapshot.get('quizzes_completed', 0)}\n"
                f"Average score: {float(snapshot.get('average_score', 0.0)) * 100:.1f}%\n"
                f"Weak areas: {', '.join([item.get('topic', 'General') for item in snapshot.get('weak_areas', [])[:5]]) or 'none'}"
            )

            user_prompt = (
                f"User message:\n{cleaned}\n\n"
                f"User profile:\n{profile_block}\n\n"
                f"Progress data:\n{progress_block}\n\n"
                f"Conversation memory:\n{history_block or 'No prior conversation memory.'}\n\n"
                f"Document context:\n{context or 'No document context supplied.'}\n\n"
                "Instructions:\n"
                "1) Answer directly and clearly.\n"
                "2) If the user asks study advice, personalize it with progress data.\n"
                "3) If no document context is present, still answer using general knowledge.\n"
                "4) If document context exists, prioritize that content when relevant."
            )

            reply = self._call_llm(
                system_prompt=self._build_system_prompt(profile, snapshot, document_info.get("title") if document_info else None),
                user_prompt=user_prompt,
            )

            sources = [
                {
                    "text": (chunk.get("text", "")[:220]).strip(),
                    "score": float(chunk.get("score", 0.0) or 0.0),
                }
                for chunk in chunks
            ]

            if chunks:
                confidence = max(0.35, min(0.92, sum(s["score"] for s in sources) / len(sources)))
            else:
                confidence = 0.6

        self._store_message(
            user_id=user_id,
            role="assistant",
            content=reply,
            document_id=document_id,
            confidence=confidence,
            sources=sources,
        )

        return {
            "response": reply,
            "sources": sources,
            "confidence": confidence,
        }

    def get_history(self, user_id: str, document_id: Optional[str] = None, limit: int = 300) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"user_id": user_id}
        if document_id:
            query["document_id"] = document_id

        rows = list(self.messages_collection.find(query).sort("created_at", 1).limit(limit))
        output: List[Dict[str, Any]] = []
        for row in rows:
            output.append(
                {
                    "chat_id": str(row.get("_id")),
                    "user_id": row.get("user_id"),
                    "document_id": row.get("document_id"),
                    "role": row.get("role", "assistant"),
                    "content": row.get("content", ""),
                    "created_at": row.get("created_at"),
                    "confidence": row.get("confidence"),
                    "sources": row.get("sources", []),
                }
            )

        return output

    @staticmethod
    def _serialize_plan(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "plan_id": str(item.get("_id")),
            "user_id": item.get("user_id"),
            "title": item.get("title", "Untitled plan"),
            "document_id": item.get("document_id"),
            "document_title": item.get("document_title"),
            "notes": item.get("notes", ""),
            "target_date": item.get("target_date"),
            "status": item.get("status", "pending"),
            "reminder_days_before": int(item.get("reminder_days_before", 2) or 2),
            "user_email": item.get("user_email"),
            "reminder_sent_at": item.get("reminder_sent_at"),
            "completed_at": item.get("completed_at"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "start_time": item.get("start_time"),
            "end_time": item.get("end_time"),
            "duration_minutes": item.get("duration_minutes"),
            "activities": item.get("activities") or [],
            "source_plan_id": item.get("source_plan_id"),
            "source_plan_title": item.get("source_plan_title"),
            "is_generated_timetable": bool(item.get("is_generated_timetable", False)),
        }

    @staticmethod
    def _parse_target_date(target_date: str) -> datetime:
        parsed = datetime.fromisoformat(target_date.replace("Z", "+00:00"))
        if parsed.tzinfo:
            parsed = parsed.astimezone().replace(tzinfo=None)
        return parsed

    def create_study_plan(
        self,
        user_id: str,
        title: str,
        target_date: str,
        document_id: Optional[str] = None,
        document_title: Optional[str] = None,
        notes: Optional[str] = None,
        reminder_days_before: int = 2,
        user_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        parsed_target = self._parse_target_date(target_date)
        now = datetime.utcnow()
        plan_id = str(uuid.uuid4())

        plan = {
            "_id": plan_id,
            "user_id": user_id,
            "title": (title or "Exam preparation").strip(),
            "document_id": document_id,
            "document_title": document_title,
            "notes": (notes or "").strip(),
            "target_date": parsed_target,
            "status": "pending",
            "reminder_days_before": max(0, min(int(reminder_days_before), 30)),
            "user_email": (user_email or "").strip() or None,
            "reminder_sent_at": None,
            "completed_at": None,
            "created_at": now,
            "updated_at": now,
        }

        self.study_plan_collection.insert_one(plan)
        return self._serialize_plan(plan)

    def list_study_plans(self, user_id: str) -> List[Dict[str, Any]]:
        rows = list(self.study_plan_collection.find({"user_id": user_id}).sort("target_date", 1).limit(200))
        return [self._serialize_plan(row) for row in rows]

    def update_study_plan_status(self, user_id: str, plan_id: str, status: str) -> Dict[str, Any]:
        raw = (status or "").strip().lower()
        if raw in {"done"}:
            normalized = "done"
        elif raw in {"in_progress", "in progress", "progress"}:
            normalized = "in_progress"
        else:
            normalized = "pending"

        update: Dict[str, Any] = {
            "status": normalized,
            "updated_at": datetime.utcnow(),
        }

        if normalized == "done":
            update["completed_at"] = datetime.utcnow()
        else:
            update["completed_at"] = None

        result = self.study_plan_collection.update_one(
            {"_id": plan_id, "user_id": user_id},
            {"$set": update},
        )
        if result.matched_count == 0:
            raise ValueError("Study plan not found")

        row = self.study_plan_collection.find_one({"_id": plan_id, "user_id": user_id})
        if not row:
            raise ValueError("Study plan not found")

        return self._serialize_plan(row)

    def delete_study_plan(self, user_id: str, plan_id: str) -> bool:
        result = self.study_plan_collection.delete_one({"_id": plan_id, "user_id": user_id})
        return result.deleted_count > 0

    def _email_configured(self) -> bool:
        return bool(
            settings.SMTP_HOST
            and settings.SMTP_PORT
            and settings.SMTP_USER
            and settings.SMTP_PASSWORD
            and settings.SMTP_FROM_EMAIL
        )

    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        if not self._email_configured():
            return False

        message = EmailMessage()
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            if settings.SMTP_USE_TLS:
                context = ssl.create_default_context()
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
                    server.starttls(context=context)
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(message)
            else:
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(message)
            return True
        except Exception:
            return False

    def get_study_plan_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        rows = list(
            self.study_plan_collection.find(
                {"user_id": user_id, "status": "pending", "notification_enabled": {"$ne": False}}
            )
            .sort("target_date", 1)
            .limit(200)
        )

        notifications: List[Dict[str, Any]] = []

        for row in rows:
            target_date = row.get("target_date")
            if not isinstance(target_date, datetime):
                continue

            seconds_left = (target_date - now).total_seconds()
            days_left = math.floor(seconds_left / 86400)
            reminder_window = int(row.get("reminder_days_before", 2) or 2)

            should_notify = days_left <= reminder_window
            if not should_notify:
                continue

            if days_left < 0:
                title = f"Plan overdue: {row.get('title', 'Study plan')}"
                message = f"Your target date was {target_date.strftime('%b %d, %Y')}. Mark as done or reschedule."
                notification_type = "overdue"
            elif days_left == 0:
                title = f"Due today: {row.get('title', 'Study plan')}"
                message = "Your study target date is today. Final revision recommended."
                notification_type = "today"
            else:
                title = f"Upcoming: {row.get('title', 'Study plan')}"
                message = f"Target date is in {days_left} day(s). Keep revising to stay on schedule."
                notification_type = "upcoming"

            notifications.append(
                {
                    "id": f"plan-note-{row.get('_id')}",
                    "type": notification_type,
                    "title": title,
                    "message": message,
                    "target_date": target_date,
                    "plan_id": str(row.get("_id")),
                }
            )

            if not row.get("reminder_sent_at") and row.get("user_email"):
                sent = self._send_email(
                    to_email=row.get("user_email"),
                    subject=title,
                    body=(
                        f"Hello,\n\n{message}\n\n"
                        f"Plan: {row.get('title', 'Study plan')}\n"
                        f"Target date: {target_date.strftime('%Y-%m-%d')}\n\n"
                        "Quiz Tutor"
                    ),
                )

                if sent:
                    self.study_plan_collection.update_one(
                        {"_id": row.get("_id"), "user_id": user_id},
                        {"$set": {"reminder_sent_at": datetime.utcnow(), "updated_at": datetime.utcnow()}},
                    )

        notifications.sort(key=lambda item: item.get("target_date") or datetime.utcnow())
        return notifications

    def generate_personalized_study_plan(
        self,
        user_id: str,
        plan_ids: List[str],
        available_days: List[str],
        study_days: int,
        hours_per_day: float,
        preferred_start_time: Optional[str],
        exam_date: str,
        learning_style: Optional[str] = "visual",
        difficulty_level: Optional[str] = "intermediate",
    ) -> Dict[str, Any]:
        """Generate a timetable for selected not-done plans using global availability inputs."""
        try:
            requested_ids = list(dict.fromkeys([str(plan_id).strip() for plan_id in plan_ids if str(plan_id).strip()]))
            if not requested_ids:
                raise ValueError("Please select at least one not-done plan")

            normalized_days = [
                day.strip().capitalize()
                for day in available_days
                if isinstance(day, str) and day.strip()
            ]
            normalized_days = list(dict.fromkeys(normalized_days))
            if not normalized_days:
                raise ValueError("Please select at least one available day")

            exam_datetime = self._parse_target_date(exam_date)
            today = datetime.utcnow().date()
            exam_date_obj = exam_datetime.date()
            days_until_exam = (exam_date_obj - today).days
            if days_until_exam <= 0:
                raise ValueError("Exam date must be in the future")

            source_rows = list(
                self.study_plan_collection.find(
                    {
                        "_id": {"$in": requested_ids},
                        "user_id": user_id,
                        "status": {"$in": ["pending", "todo", "in_progress"]},
                    }
                )
            )

            source_plan_by_id = {str(row.get("_id")): row for row in source_rows}
            missing_or_done = [plan_id for plan_id in requested_ids if plan_id not in source_plan_by_id]
            if missing_or_done:
                raise ValueError("Some selected plans are missing or already done. Please refresh and retry.")

            max_sessions = min(int(study_days), days_until_exam)
            if max_sessions <= 0:
                raise ValueError("No available study days before exam date")

            start_time = (preferred_start_time or "09:00").strip()
            if not re.match(r"^\d{2}:\d{2}$", start_time):
                start_time = "09:00"

            duration_minutes = max(30, int(float(hours_per_day) * 60))
            available_days_str = ", ".join(normalized_days)
            plan_lines = "\n".join(
                [f"- plan_id: {plan_id} | title: {source_plan_by_id[plan_id].get('title', 'Study plan')}" for plan_id in requested_ids]
            )

            prompt = f"""Create a calendar-style timetable from existing not-done plans.

Selected Plans:
{plan_lines}

Constraints:
- Available weekdays: {available_days_str}
- Total study sessions to generate: {max_sessions}
- Session duration: {hours_per_day} hours
- Preferred start time: {start_time}
- Exam date: {exam_date_obj.isoformat()}
- Learning style: {learning_style}
- Difficulty level: {difficulty_level}

Return strict JSON only (no markdown) in this format:
{{
  "timetable": [
    {{
      "date": "YYYY-MM-DD",
      "plan_id": "one of the selected plan_id values",
      "title": "short session title",
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "notes": "short note"
    }}
  ]
}}

Rules:
1) Use only selected plan_id values.
2) Distribute sessions fairly across plans.
3) Date must be on or after tomorrow and on/before exam date.
4) Date must match one of available weekdays.
5) Keep exactly {max_sessions} sessions when possible.
"""

            client = Groq(api_key=settings.GROQ_API_KEY)
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You generate valid JSON timetables."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.45,
                max_tokens=1800,
            )

            response_text = (response.choices[0].message.content or "").strip()
            json_match = re.search(r'\{[\s\S]*"timetable"[\s\S]*\}', response_text)
            if not json_match:
                generated = self._create_fallback_timetable(
                    user_id=user_id,
                    source_plan_by_id=source_plan_by_id,
                    available_days=normalized_days,
                    study_days=max_sessions,
                    duration_minutes=duration_minutes,
                    preferred_start_time=start_time,
                    exam_date_obj=exam_date_obj,
                )
                return {
                    "generated_schedules": generated,
                    "total_sessions": len(generated),
                    "message": f"Generated timetable with {len(generated)} session(s).",
                }

            try:
                schedule_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                generated = self._create_fallback_timetable(
                    user_id=user_id,
                    source_plan_by_id=source_plan_by_id,
                    available_days=normalized_days,
                    study_days=max_sessions,
                    duration_minutes=duration_minutes,
                    preferred_start_time=start_time,
                    exam_date_obj=exam_date_obj,
                )
                return {
                    "generated_schedules": generated,
                    "total_sessions": len(generated),
                    "message": f"Generated timetable with {len(generated)} session(s).",
                }

            generated: List[Dict[str, Any]] = []
            now = datetime.utcnow()

            for entry in schedule_data.get("timetable", []) or []:
                source_plan_id = str(entry.get("plan_id") or "").strip()
                source_plan = source_plan_by_id.get(source_plan_id)
                if not source_plan:
                    continue

                date_str = str(entry.get("date") or "").strip()
                try:
                    target_date = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    continue

                if target_date.date() > exam_date_obj or target_date.date() <= today:
                    continue
                if target_date.strftime("%A") not in normalized_days:
                    continue

                raw_start_time = str(entry.get("start_time") or start_time).strip()
                if not re.match(r"^\d{2}:\d{2}$", raw_start_time):
                    raw_start_time = start_time

                try:
                    start_dt = datetime.strptime(raw_start_time, "%H:%M")
                    raw_end_time = (entry.get("end_time") or "").strip()
                    if not re.match(r"^\d{2}:\d{2}$", raw_end_time):
                        raw_end_time = (start_dt + timedelta(minutes=duration_minutes)).strftime("%H:%M")
                except ValueError:
                    raw_start_time = start_time
                    raw_end_time = "11:00"

                source_title = str(source_plan.get("title") or "Study plan")
                session_record = {
                    "_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "title": str(entry.get("title") or f"Study session: {source_title}"),
                    "source_plan_id": source_plan_id,
                    "source_plan_title": source_title,
                    "document_id": source_plan.get("document_id"),
                    "document_title": source_plan.get("document_title"),
                    "target_date": target_date,
                    "start_time": raw_start_time,
                    "end_time": raw_end_time,
                    "duration_minutes": duration_minutes,
                    "activities": [
                        {
                            "name": f"Study {source_title}",
                            "duration_minutes": duration_minutes,
                            "status": "todo",
                        }
                    ],
                    "notes": str(entry.get("notes") or f"Generated from: {source_title}"),
                    "status": "pending",
                    "reminder_days_before": 0,
                    "notification_enabled": False,
                    "is_generated_timetable": True,
                    "created_at": now,
                    "updated_at": now,
                }

                self.study_plan_collection.insert_one(session_record)
                generated.append(self._serialize_plan(session_record))

            if not generated:
                generated = self._create_fallback_timetable(
                    user_id=user_id,
                    source_plan_by_id=source_plan_by_id,
                    available_days=normalized_days,
                    study_days=max_sessions,
                    duration_minutes=duration_minutes,
                    preferred_start_time=start_time,
                    exam_date_obj=exam_date_obj,
                )

            return {
                "generated_schedules": generated,
                "total_sessions": len(generated),
                "message": f"Generated timetable with {len(generated)} session(s).",
            }

        except Exception as exc:
            print(f"❌ Error generating personalized study plan: {exc}")
            raise ValueError(f"Failed to generate study plan: {str(exc)}")

    def _create_fallback_timetable(
        self,
        user_id: str,
        source_plan_by_id: Dict[str, Dict[str, Any]],
        available_days: List[str],
        study_days: int,
        duration_minutes: int,
        preferred_start_time: str,
        exam_date_obj: datetime.date,
    ) -> List[Dict[str, Any]]:
        """Create a deterministic timetable when LLM JSON output is unavailable."""
        generated: List[Dict[str, Any]] = []
        if not source_plan_by_id:
            return generated

        day_set = set(available_days)
        source_plan_ids = list(source_plan_by_id.keys())
        now = datetime.utcnow()

        try:
            start_dt = datetime.strptime(preferred_start_time, "%H:%M")
            fallback_end_time = (start_dt + timedelta(minutes=duration_minutes)).strftime("%H:%M")
        except ValueError:
            preferred_start_time = "09:00"
            fallback_end_time = "11:00"

        current_date = datetime.utcnow().date() + timedelta(days=1)
        round_robin_idx = 0

        while current_date <= exam_date_obj and len(generated) < study_days:
            if current_date.strftime("%A") in day_set:
                source_plan_id = source_plan_ids[round_robin_idx % len(source_plan_ids)]
                source_plan = source_plan_by_id[source_plan_id]
                source_title = str(source_plan.get("title") or "Study plan")

                session_record = {
                    "_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "title": f"Study session: {source_title}",
                    "source_plan_id": source_plan_id,
                    "source_plan_title": source_title,
                    "document_id": source_plan.get("document_id"),
                    "document_title": source_plan.get("document_title"),
                    "target_date": datetime.combine(current_date, datetime.min.time()),
                    "start_time": preferred_start_time,
                    "end_time": fallback_end_time,
                    "duration_minutes": duration_minutes,
                    "activities": [
                        {
                            "name": f"Study {source_title}",
                            "duration_minutes": duration_minutes,
                            "status": "todo",
                        }
                    ],
                    "notes": f"Generated from: {source_title}",
                    "status": "pending",
                    "reminder_days_before": 0,
                    "notification_enabled": False,
                    "is_generated_timetable": True,
                    "created_at": now,
                    "updated_at": now,
                }

                self.study_plan_collection.insert_one(session_record)
                generated.append(self._serialize_plan(session_record))
                round_robin_idx += 1

            current_date += timedelta(days=1)

        return generated
