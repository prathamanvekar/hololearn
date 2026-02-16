"""
LLM Service Module
==================
Handles interaction with Groq API for:
- Chat responses
- Translation
- Quiz generation
- Explanations
"""

import json
from typing import List, Dict, Optional
from groq import Groq

from backend.config import GROQ_API_KEY, ModelConfig, SUPPORTED_LANGUAGES


class LLMService:
    """
    LLM Service using Groq API
    """

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = ModelConfig.GROQ_MODEL
        print("✅ LLM Service initialized!")

    def _call_llm(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Make a call to the Groq LLM

        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum response tokens

        Returns:
            LLM response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ LLM Error: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def chat_with_context(
        self,
        query: str,
        context: str,
        chat_history: List[Dict] = None,
        language: str = "en",
        student_name: str = "Student"
    ) -> str:
        """
        Generate a response using RAG context

        Args:
            query: User query
            context: Retrieved context from documents
            chat_history: Previous conversation history
            language: Response language
            student_name: Student's name for personalization

        Returns:
            Generated response
        """
        lang_name = SUPPORTED_LANGUAGES.get(language, "English")

        system_prompt = f"""You are HoloLearn, an intelligent and friendly AI learning assistant.
You help students understand concepts by providing clear, personalized explanations.

Guidelines:
1. Use the provided context to answer questions accurately
2. If the context doesn't contain relevant information, say so honestly
3. Explain concepts in simple, easy-to-understand language
4. Use examples and analogies when helpful
5. Be encouraging and supportive
6. Respond in {lang_name}
7. Address the student as {student_name}

Context from study materials:
---
{context if context else "No specific context available. Use your general knowledge."}
---"""

        messages = [{"role": "system", "content": system_prompt}]

        # Add chat history
        if chat_history:
            for msg in chat_history[-6:]:  # Last 6 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        # Add current query
        messages.append({"role": "user", "content": query})

        return self._call_llm(messages, temperature=0.7)

    def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Translate text between languages

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Translated text
        """
        source_name = SUPPORTED_LANGUAGES.get(source_lang, "English")
        target_name = SUPPORTED_LANGUAGES.get(target_lang, "Hindi")

        messages = [
            {
                "role": "system",
                "content": f"You are a professional translator. Translate the following text from {source_name} to {target_name}. Only provide the translation, no explanations."
            },
            {
                "role": "user",
                "content": text
            }
        ]

        return self._call_llm(messages, temperature=0.3)

    def generate_quiz(
        self,
        content: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        language: str = "en",
        avoid_questions: Optional[List[str]] = None,
        nonce: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate quiz questions from content

        Args:
            content: Source content for quiz
            num_questions: Number of questions
            difficulty: Difficulty level
            language: Language for questions

        Returns:
            List of question dictionaries
        """
        lang_name = SUPPORTED_LANGUAGES.get(language, "English")

        avoid_block = ""
        cleaned_avoid = [q.strip() for q in (avoid_questions or []) if (q or "").strip()]
        if cleaned_avoid:
            # Keep this small to avoid token blowups.
            trimmed = []
            total_chars = 0
            for item in cleaned_avoid[:8]:
                snippet = " ".join(item.split())
                snippet = snippet[:220]
                if not snippet:
                    continue
                total_chars += len(snippet)
                if total_chars > 1200:
                    break
                trimmed.append(snippet)
            if trimmed:
                avoid_block = "\nDo NOT repeat any of these previously asked questions (rephrase counts as repetition):\n- " + "\n- ".join(trimmed) + "\n"

        nonce_block = f"\nUnique session nonce: {nonce}\n" if nonce else ""

        prompt = f"""Based on the following content, generate {num_questions} multiple-choice quiz questions.

Difficulty: {difficulty}
Language: {lang_name}
    {nonce_block}{avoid_block}

    Rules:
    1. Questions must be meaningfully different from each other and from the avoid-list.
    2. Prefer different angles: definitions vs examples vs edge-cases vs applications.
    3. Keep options plausible and avoid trivial giveaways.

Content:
---
{content}
---

Generate questions in the following JSON format:
[
  {{
    "question": "Question text here",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "correct_answer": "A",
    "explanation": "Brief explanation of why this is correct"
  }}
]

Only return valid JSON, no other text."""

        messages = [
            {"role": "system", "content": "You are a quiz generator. Generate educational quiz questions in valid JSON format."},
            {"role": "user", "content": prompt}
        ]

        # Slightly higher temperature encourages variety, while constraints keep structure.
        response = self._call_llm(messages, temperature=0.65)

        # Parse JSON response
        try:
            # Find JSON in response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                questions = json.loads(json_str)
                if isinstance(questions, list):
                    return questions[: max(1, int(num_questions or 1))]
                return []
        except json.JSONDecodeError:
            pass

        # Return empty list if parsing fails
        return []

    def generate_summary(
        self,
        content: str,
        language: str = "en",
        max_points: int = 5
    ) -> str:
        """
        Generate a summary of content

        Args:
            content: Content to summarize
            language: Language for summary
            max_points: Maximum bullet points

        Returns:
            Summary text
        """
        lang_name = SUPPORTED_LANGUAGES.get(language, "English")

        prompt = f"""Summarize the following content in {lang_name}.
Provide a clear, concise summary with up to {max_points} key points.

Content:
---
{content}
---

Format as bullet points."""

        messages = [
            {"role": "system", "content": "You are an expert summarizer. Create clear, educational summaries."},
            {"role": "user", "content": prompt}
        ]

        return self._call_llm(messages, temperature=0.5)

    def explain_concept(
        self,
        concept: str,
        context: str = "",
        language: str = "en",
        level: str = "intermediate"
    ) -> str:
        """
        Generate a detailed explanation of a concept

        Args:
            concept: Concept to explain
            context: Additional context
            language: Language for explanation
            level: Explanation level (beginner/intermediate/advanced)

        Returns:
            Explanation text
        """
        lang_name = SUPPORTED_LANGUAGES.get(language, "English")

        prompt = f"""Explain the concept of "{concept}" in {lang_name}.

Level: {level}
{f'Additional context: {context}' if context else ''}

Provide:
1. A clear definition
2. Key points to understand
3. A simple example or analogy
4. Why it's important

Make it engaging and easy to understand."""

        messages = [
            {"role": "system", "content": "You are an expert teacher who explains concepts clearly and engagingly."},
            {"role": "user", "content": prompt}
        ]

        return self._call_llm(messages, temperature=0.7)

    def get_recommendations(
        self,
        student_performance: Dict,
        available_topics: List[str],
        language: str = "en"
    ) -> Dict:
        """
        Generate personalized study recommendations

        Args:
            student_performance: Dict with performance data
            available_topics: List of available topics
            language: Language for recommendations

        Returns:
            Recommendations dictionary
        """
        lang_name = SUPPORTED_LANGUAGES.get(language, "English")

        prompt = f"""Based on the student's performance data, provide study recommendations in {lang_name}.

Performance Data:
{json.dumps(student_performance, indent=2)}

Available Topics:
{', '.join(available_topics)}

Provide recommendations in JSON format:
{{
  "priority_topics": ["topic1", "topic2"],
  "strengths": ["area1", "area2"],
  "areas_to_improve": ["area1", "area2"],
  "study_tips": ["tip1", "tip2"],
  "recommended_next_steps": ["step1", "step2"]
}}

Only return valid JSON."""

        messages = [
            {"role": "system", "content": "You are an educational advisor providing personalized study recommendations."},
            {"role": "user", "content": prompt}
        ]

        response = self._call_llm(messages, temperature=0.5)

        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except json.JSONDecodeError:
            pass

        return {
            "priority_topics": [],
            "strengths": [],
            "areas_to_improve": [],
            "study_tips": ["Keep practicing regularly"],
            "recommended_next_steps": ["Review your recent topics"]
        }

    def generate_bilingual_response(
        self,
        query: str,
        context: str,
        primary_lang: str = "en",
        secondary_lang: str = "hi"
    ) -> Dict[str, str]:
        """
        Generate response in both languages

        Args:
            query: User query
            context: RAG context
            primary_lang: Primary language
            secondary_lang: Secondary language

        Returns:
            Dict with responses in both languages
        """
        primary_name = SUPPORTED_LANGUAGES.get(primary_lang, "English")
        secondary_name = SUPPORTED_LANGUAGES.get(secondary_lang, "Hindi")

        prompt = f"""Answer the following question using the provided context.
Provide the answer in BOTH {primary_name} and {secondary_name}.

Context:
---
{context if context else "No specific context available."}
---

Question: {query}

Format your response as:
[{primary_name.upper()}]
(Your answer in {primary_name})

[{secondary_name.upper()}]
(Your answer in {secondary_name})"""

        messages = [
            {"role": "system", "content": "You are a bilingual educational assistant. Always provide responses in both requested languages."},
            {"role": "user", "content": prompt}
        ]

        response = self._call_llm(messages, temperature=0.7)

        # Parse bilingual response
        result = {
            primary_lang: "",
            secondary_lang: ""
        }

        # Try to split by language markers
        primary_marker = f"[{primary_name.upper()}]"
        secondary_marker = f"[{secondary_name.upper()}]"

        if primary_marker in response and secondary_marker in response:
            parts = response.split(secondary_marker)
            if len(parts) >= 2:
                result[primary_lang] = parts[0].replace(primary_marker, "").strip()
                result[secondary_lang] = parts[1].strip()
        else:
            # If parsing fails, translate
            result[primary_lang] = response
            result[secondary_lang] = self.translate_text(response, primary_lang, secondary_lang)

        return result


# Singleton instance
llm_service = LLMService()
