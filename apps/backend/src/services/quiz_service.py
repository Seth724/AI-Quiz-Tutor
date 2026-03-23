"""
Quiz Service

Generates quizzes from document content using Groq LLM
"""

import os
import json
import re
from typing import List, Dict, Any
from difflib import SequenceMatcher
from groq import Groq
from pymongo import MongoClient
from datetime import datetime
import uuid

from config import settings


class QuizService:
    """Service for quiz generation and grading"""
    
    def __init__(self):
        """Initialize quiz service"""
        # Groq LLM client
        self.llm = Groq(api_key=settings.GROQ_API_KEY)
        
        # MongoDB connection
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.db = self.mongo_client[settings.MONGODB_DATABASE]
        self.quizzes_collection = self.db["quizzes"]
        self.attempts_collection = self.db["attempts"]
    
    def generate_quiz(
        self,
        document_content: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        question_type: str = "multiple_choice",
        max_context_chars: int = 8000
    ) -> Dict[str, Any]:
        """
        Generate quiz from document content using Groq LLM
        
        Handles large documents by limiting context size to avoid token limits.
        """
        try:
            print(f"Generating {num_questions} {difficulty} questions...")
            
            # Limit context size to avoid overwhelming Groq and token limits
            if len(document_content) > max_context_chars:
                print(f"⚠️  Context too large ({len(document_content)}), truncating to {max_context_chars}...")
                document_content = document_content[:max_context_chars] + "...[content truncated]"
            
            schema_example = """
{
    "questions": [
        {
            "id": "q1",
            "question": "Question text here",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "explanation": "Explain core concept, why answer is correct, and one practical takeaway.",
            "topic": "Topic name"
        }
    ]
}
""".strip()

            if question_type == "short_answer":
                schema_example = """
{
    "questions": [
        {
            "id": "q1",
            "question": "Short-answer question text here",
            "correct_answer": "Expected concise answer",
            "explanation": "Detailed explanation with concept, key terms, and practical usage.",
            "topic": "Topic name"
        }
    ]
}
""".strip()

            # Prompt for quiz generation
            prompt = f"""Based on the following content, generate {num_questions} {difficulty} {question_type} questions.

CONTENT:
{document_content}

Generate questions in this JSON format with EXACTLY {num_questions} questions:
{schema_example}

CRITICAL REQUIREMENTS:
- Return ONLY valid JSON, NO other text
- Generate EXACTLY {num_questions} questions
- Difficulty: {difficulty}
- Type: {question_type}
- Do NOT include markdown formatting or code blocks
- Do NOT prefix with "json" or ```

QUALITY REQUIREMENTS:
- Questions must test understanding, not just trivial recall.
- Explanations must be detailed (2-4 sentences) and educational.
- For explanations: include concept summary, why answer is correct, and one study tip.
- If type is short_answer, do not include options.
- If type is multiple_choice, include exactly 4 options.
"""
            
            # Call Groq LLM with retry
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = self.llm.chat.completions.create(
                        model=settings.LLM_MODEL,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert educator. Respond ONLY with valid JSON, no explanations."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.7,
                        max_tokens=3000
                    )
                    
                    if not response or not response.choices or not response.choices[0].message:
                        raise ValueError(f"Empty response from Groq (attempt {attempt+1})")
                    
                    content = response.choices[0].message.content
                    if not content or not content.strip():
                        raise ValueError(f"Empty message content (attempt {attempt+1})")
                    
                    # Clean response (remove markdown code blocks if present)
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    # Parse response
                    quiz_data = json.loads(content)
                    
                    # Validate we got questions
                    if not quiz_data.get("questions"):
                        raise ValueError("No questions in response")
                    
                    normalized_questions: List[Dict[str, Any]] = []
                    for idx, question in enumerate(quiz_data.get("questions", [])[:num_questions], start=1):
                        q_id = question.get("id") or f"q{idx}"
                        q_text = (question.get("question") or "").strip()
                        if not q_text:
                            continue

                        normalized: Dict[str, Any] = {
                            "id": q_id,
                            "question": q_text,
                            "correct_answer": (question.get("correct_answer") or "").strip(),
                            "explanation": (question.get("explanation") or "").strip(),
                            "topic": (question.get("topic") or "General").strip() or "General",
                        }

                        if question_type == "multiple_choice":
                            options = question.get("options") or []
                            options = [str(option).strip() for option in options if str(option).strip()]
                            if len(options) < 2:
                                continue

                            # Keep at most 4 options to control UI complexity.
                            normalized["options"] = options[:4]

                            # Ensure correct answer exists in options for consistent grading.
                            if normalized["correct_answer"] and normalized["correct_answer"] not in normalized["options"]:
                                normalized["options"][0] = normalized["correct_answer"]

                        normalized_questions.append(normalized)

                    if not normalized_questions:
                        raise ValueError("Model returned invalid question payload")

                    # Add metadata
                    quiz = {
                        "_id": str(uuid.uuid4()),
                        "questions": normalized_questions,
                        "total_questions": len(normalized_questions),
                        "difficulty": difficulty,
                        "question_type": question_type,
                        "created_at": datetime.now()
                    }
                    
                    print(f"✅ Generated {len(quiz['questions'])} questions")
                    return quiz
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON parse error (attempt {attempt+1}): {str(e)[:100]}")
                    if attempt < max_retries - 1:
                        print("    Retrying...")
                        continue
                    raise ValueError(f"Failed to parse Groq response: {str(e)[:80]}")
                except Exception as e:
                    print(f"⚠️  Error on attempt {attempt+1}: {str(e)[:100]}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)
                        continue
                    raise
            
        except Exception as e:
            print(f"❌ Error generating quiz: {e}")
            raise
    
    def save_quiz(self, quiz: Dict[str, Any], document_id: str, user_id: str) -> str:
        """Save quiz to MongoDB"""
        try:
            quiz["document_id"] = document_id
            quiz["user_id"] = user_id
            quiz["created_at"] = datetime.now()
            
            result = self.quizzes_collection.insert_one(quiz)
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Error saving quiz: {e}")
            raise
    
    def get_quiz(self, quiz_id: str) -> Dict[str, Any]:
        """Get quiz by ID"""
        try:
            quiz = self.quizzes_collection.find_one({"_id": quiz_id})
            if quiz:
                quiz["_id"] = str(quiz["_id"])
            return quiz
        except Exception as e:
            print(f"❌ Error getting quiz: {e}")
            return None
    
    def grade_quiz(self, quiz_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
        """
        Grade quiz and identify weak areas
        """
        try:
            # Get quiz
            quiz = self.get_quiz(quiz_id)
            if not quiz:
                raise ValueError("Quiz not found")
            
            # Grade each question
            correct_count = 0
            topic_scores = {}
            graded_questions = []
            question_type = quiz.get("question_type", "multiple_choice")
            
            for question in quiz["questions"]:
                q_id = question["id"]
                user_answer = answers.get(q_id, "")
                correct_answer = question["correct_answer"]
                topic = question.get("topic", "General")
                
                # Check if correct
                is_correct = self._is_answer_correct(user_answer, correct_answer, question_type)
                if is_correct:
                    correct_count += 1
                
                # Track topic performance
                if topic not in topic_scores:
                    topic_scores[topic] = {"correct": 0, "total": 0}
                topic_scores[topic]["total"] += 1
                if is_correct:
                    topic_scores[topic]["correct"] += 1
                
                # Add to graded questions
                graded_questions.append({
                    "question_id": q_id,
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "is_correct": is_correct,
                    "explanation": question["explanation"]
                })
            
            # Calculate score
            total_questions = len(quiz["questions"])
            score = correct_count / total_questions if total_questions > 0 else 0.0
            
            # Identify weak areas (topics with < 50% accuracy)
            weak_areas = []
            for topic, scores in topic_scores.items():
                accuracy = scores["correct"] / scores["total"]
                if accuracy < 0.5:
                    weak_areas.append({
                        "topic": topic,
                        "accuracy": accuracy,
                        "correct": scores["correct"],
                        "total": scores["total"]
                    })
            
            # Generate recommendations
            recommendations = self._generate_recommendations(weak_areas, quiz)
            
            # Create result
            result = {
                "quiz_id": quiz_id,
                "score": score,
                "correct_count": correct_count,
                "total_questions": total_questions,
                "percentage": f"{score * 100:.1f}%",
                "weak_areas": weak_areas,
                "recommendations": recommendations,
                "topic_performance": topic_scores,
                "graded_questions": graded_questions,
                "completed_at": datetime.now()
            }
            
            print(f"✅ Quiz graded: {score * 100:.1f}%")
            
            return result
            
        except Exception as e:
            print(f"❌ Error grading quiz: {e}")
            raise
    
    def _generate_recommendations(self, weak_areas: List[Dict], quiz: Dict) -> List[str]:
        """Generate study recommendations based on performance"""
        recommendations = []
        
        if not weak_areas:
            recommendations.append("Great job! Review all topics to maintain your knowledge.")
        else:
            for area in weak_areas:
                recommendations.append(
                    f"Focus on '{area['topic']}' - accuracy: {area['accuracy']*100:.0f}%"
                )
        
        # Add general recommendations based on score
        total_questions = quiz.get("total_questions", 0)
        if total_questions < 3:
            recommendations.append("Try a longer quiz for better assessment")
        
        return recommendations

    @staticmethod
    def _normalize_answer(value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").strip().lower())

    def _is_answer_correct(self, user_answer: str, correct_answer: str, question_type: str) -> bool:
        """Grade answers with tolerant matching for short-answer questions."""
        user_norm = self._normalize_answer(user_answer)
        correct_norm = self._normalize_answer(correct_answer)

        if not user_norm or not correct_norm:
            return False

        if question_type == "multiple_choice":
            return user_norm == correct_norm

        if user_norm == correct_norm:
            return True

        if correct_norm in user_norm:
            return True

        similarity = SequenceMatcher(None, user_norm, correct_norm).ratio()
        return similarity >= 0.72
    
    def _generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer using Groq LLM with RAG context
        """
        try:
            prompt = f"""
You must answer ONLY using the provided context.

CONTEXT:
{context}

QUESTION: {question}

Rules:
- Do not invent facts not present in context.
- If context is insufficient, answer exactly: "I don't have enough information about that in the document."
- Keep answer concise and specific to the question.
- If listing items (like tables/sections), list only items explicitly present in context.

Answer:
"""
            
            response = self.llm.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strict document-grounded tutor. Never hallucinate. Use only context."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Error generating answer: {e}")
            return "I couldn't generate an answer. Please try again."
    
    def save_attempt(self, attempt: Dict[str, Any]) -> str:
        """Save quiz attempt to MongoDB"""
        try:
            result = self.attempts_collection.insert_one(attempt)
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Error saving attempt: {e}")
            raise
    
    def get_user_attempts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all attempts for a user"""
        try:
            attempts = list(self.attempts_collection.find({"user_id": user_id}))
            for attempt in attempts:
                attempt["_id"] = str(attempt["_id"])
            return attempts
        except Exception as e:
            print(f"❌ Error getting attempts: {e}")
            return []


# Singleton instance
quiz_service = QuizService()
