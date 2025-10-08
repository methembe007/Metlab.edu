"""
AI-powered content generation services for the learning platform.
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import openai
except ImportError:
    openai = None

from django.conf import settings
from django.utils import timezone

from .models import UploadedContent, GeneratedSummary, GeneratedQuiz, Flashcard

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass


class SummaryType(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    DETAILED = "detailed"


class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_IN_BLANK = "fill_in_blank"


@dataclass
class QuizQuestion:
    question: str
    question_type: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: str


@dataclass
class FlashcardData:
    front: str
    back: str
    concept: str
    difficulty: str


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        self.client = None
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 2000
        self.temperature = 0.7
        
        # Initialize OpenAI client if available
        if openai and hasattr(settings, 'OPENAI_API_KEY'):
            try:
                openai.api_key = settings.OPENAI_API_KEY
                self.client = openai
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
        else:
            logger.warning("OpenAI not available or API key not configured")
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.client is not None
    
    def generate_completion(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Generate completion using OpenAI API
        
        Args:
            prompt: Input prompt for the AI
            max_tokens: Maximum tokens to generate
            
        Returns:
            str: Generated completion
            
        Raises:
            AIServiceError: If API call fails
        """
        if not self.is_available():
            raise AIServiceError("OpenAI service not available")
        
        try:
            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise AIServiceError(f"AI generation failed: {str(e)}")


class ConceptExtractor:
    """Service for extracting key concepts from content"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    def extract_concepts(self, text: str, max_concepts: int = 10) -> List[str]:
        """
        Extract key concepts from text content
        
        Args:
            text: Input text content
            max_concepts: Maximum number of concepts to extract
            
        Returns:
            List[str]: List of key concepts
        """
        if not text.strip():
            return []
        
        if self.openai_service.is_available():
            return self._extract_with_ai(text, max_concepts)
        else:
            return self._extract_with_fallback(text, max_concepts)
    
    def _extract_with_ai(self, text: str, max_concepts: int) -> List[str]:
        """Extract concepts using AI"""
        prompt = f"""
        Analyze the following text and extract the {max_concepts} most important key concepts, terms, or topics.
        Return only a JSON array of strings, with each concept being a short phrase (1-4 words).
        Focus on educational concepts that would be important for learning and testing.
        
        Text to analyze:
        {text[:3000]}  # Limit text length for API
        
        Return format: ["concept1", "concept2", "concept3", ...]
        """
        
        try:
            response = self.openai_service.generate_completion(prompt, max_tokens=500)
            
            # Parse JSON response
            concepts = json.loads(response)
            
            if isinstance(concepts, list):
                return [str(concept).strip() for concept in concepts[:max_concepts]]
            else:
                logger.warning("AI returned non-list response for concept extraction")
                return self._extract_with_fallback(text, max_concepts)
                
        except Exception as e:
            logger.error(f"AI concept extraction failed: {str(e)}")
            return self._extract_with_fallback(text, max_concepts)
    
    def _extract_with_fallback(self, text: str, max_concepts: int) -> List[str]:
        """Fallback concept extraction using simple text analysis"""
        # Simple keyword extraction based on frequency and importance
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)  # Capitalized terms
        
        # Count frequency
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top concepts
        sorted_concepts = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        concepts = [concept for concept, freq in sorted_concepts[:max_concepts]]
        
        return concepts


class SummaryGenerator:
    """Service for generating summaries of different lengths"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    def generate_summary(self, text: str, summary_type: SummaryType) -> str:
        """
        Generate summary of specified type
        
        Args:
            text: Input text content
            summary_type: Type of summary to generate
            
        Returns:
            str: Generated summary
        """
        if not text.strip():
            return ""
        
        if self.openai_service.is_available():
            return self._generate_with_ai(text, summary_type)
        else:
            return self._generate_with_fallback(text, summary_type)
    
    def _generate_with_ai(self, text: str, summary_type: SummaryType) -> str:
        """Generate summary using AI"""
        length_specs = {
            SummaryType.SHORT: "2-3 sentences, focusing on the main point",
            SummaryType.MEDIUM: "1-2 paragraphs, covering key points and important details",
            SummaryType.DETAILED: "3-4 paragraphs, comprehensive coverage with examples and context"
        }
        
        prompt = f"""
        Create a {summary_type.value} summary of the following text.
        Length requirement: {length_specs[summary_type]}
        
        Make the summary educational and suitable for students learning this material.
        Focus on the most important concepts and information.
        
        Text to summarize:
        {text[:4000]}  # Limit text length for API
        
        Summary:
        """
        
        try:
            return self.openai_service.generate_completion(prompt, max_tokens=800)
        except Exception as e:
            logger.error(f"AI summary generation failed: {str(e)}")
            return self._generate_with_fallback(text, summary_type)
    
    def _generate_with_fallback(self, text: str, summary_type: SummaryType) -> str:
        """Fallback summary generation using simple text processing"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return "No content available for summary."
        
        # Select sentences based on summary type
        if summary_type == SummaryType.SHORT:
            selected = sentences[:2]
        elif summary_type == SummaryType.MEDIUM:
            selected = sentences[:min(5, len(sentences))]
        else:  # DETAILED
            selected = sentences[:min(10, len(sentences))]
        
        return '. '.join(selected) + '.'


class QuizGenerator:
    """Service for generating quizzes from content"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    def generate_quiz(self, text: str, num_questions: int = 5, difficulty: str = "medium") -> List[QuizQuestion]:
        """
        Generate quiz questions from text content
        
        Args:
            text: Input text content
            num_questions: Number of questions to generate
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            List[QuizQuestion]: List of generated quiz questions
        """
        if not text.strip():
            return []
        
        if self.openai_service.is_available():
            return self._generate_with_ai(text, num_questions, difficulty)
        else:
            return self._generate_with_fallback(text, num_questions, difficulty)
    
    def _generate_with_ai(self, text: str, num_questions: int, difficulty: str) -> List[QuizQuestion]:
        """Generate quiz using AI"""
        prompt = f"""
        Create {num_questions} quiz questions from the following text.
        Difficulty level: {difficulty}
        
        Generate a mix of question types:
        - Multiple choice (4 options)
        - True/False
        - Short answer
        
        Return the questions in JSON format with this structure:
        [
            {{
                "question": "Question text here?",
                "type": "multiple_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "explanation": "Brief explanation of why this is correct",
                "difficulty": "{difficulty}"
            }},
            ...
        ]
        
        Text content:
        {text[:3000]}
        
        Questions:
        """
        
        try:
            response = self.openai_service.generate_completion(prompt, max_tokens=1500)
            questions_data = json.loads(response)
            
            questions = []
            for q_data in questions_data:
                question = QuizQuestion(
                    question=q_data.get('question', ''),
                    question_type=q_data.get('type', 'multiple_choice'),
                    options=q_data.get('options', []),
                    correct_answer=q_data.get('correct_answer', ''),
                    explanation=q_data.get('explanation', ''),
                    difficulty=q_data.get('difficulty', difficulty)
                )
                questions.append(question)
            
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"AI quiz generation failed: {str(e)}")
            return self._generate_with_fallback(text, num_questions, difficulty)
    
    def _generate_with_fallback(self, text: str, num_questions: int, difficulty: str) -> List[QuizQuestion]:
        """Fallback quiz generation using simple text processing"""
        # Simple fallback: create basic questions from sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        questions = []
        for i, sentence in enumerate(sentences[:num_questions]):
            # Create a simple fill-in-the-blank question
            words = sentence.split()
            if len(words) > 5:
                # Remove a key word (usually a noun or important term)
                key_word_idx = len(words) // 2
                key_word = words[key_word_idx]
                question_text = sentence.replace(key_word, "______", 1)
                
                question = QuizQuestion(
                    question=f"Fill in the blank: {question_text}",
                    question_type="fill_in_blank",
                    options=[],
                    correct_answer=key_word,
                    explanation=f"The correct answer is '{key_word}' based on the context.",
                    difficulty=difficulty
                )
                questions.append(question)
        
        return questions


class FlashcardGenerator:
    """Service for generating flashcards from content"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.concept_extractor = ConceptExtractor()
    
    def generate_flashcards(self, text: str, num_cards: int = 10) -> List[FlashcardData]:
        """
        Generate flashcards from text content
        
        Args:
            text: Input text content
            num_cards: Number of flashcards to generate
            
        Returns:
            List[FlashcardData]: List of generated flashcards
        """
        if not text.strip():
            return []
        
        # First extract key concepts
        concepts = self.concept_extractor.extract_concepts(text, num_cards)
        
        if self.openai_service.is_available():
            return self._generate_with_ai(text, concepts)
        else:
            return self._generate_with_fallback(text, concepts)
    
    def _generate_with_ai(self, text: str, concepts: List[str]) -> List[FlashcardData]:
        """Generate flashcards using AI"""
        concepts_str = ", ".join(concepts)
        
        prompt = f"""
        Create flashcards for the following concepts based on the provided text.
        Concepts: {concepts_str}
        
        For each concept, create a flashcard with:
        - Front: A question or term
        - Back: The answer or definition
        - Make them educational and suitable for studying
        
        Return in JSON format:
        [
            {{
                "front": "What is...?",
                "back": "Definition or explanation",
                "concept": "concept name",
                "difficulty": "easy|medium|hard"
            }},
            ...
        ]
        
        Text content:
        {text[:3000]}
        
        Flashcards:
        """
        
        try:
            response = self.openai_service.generate_completion(prompt, max_tokens=1200)
            cards_data = json.loads(response)
            
            flashcards = []
            for card_data in cards_data:
                flashcard = FlashcardData(
                    front=card_data.get('front', ''),
                    back=card_data.get('back', ''),
                    concept=card_data.get('concept', ''),
                    difficulty=card_data.get('difficulty', 'medium')
                )
                flashcards.append(flashcard)
            
            return flashcards
            
        except Exception as e:
            logger.error(f"AI flashcard generation failed: {str(e)}")
            return self._generate_with_fallback(text, concepts)
    
    def _generate_with_fallback(self, text: str, concepts: List[str]) -> List[FlashcardData]:
        """Fallback flashcard generation using simple text processing"""
        flashcards = []
        
        for concept in concepts:
            # Find sentences containing the concept
            sentences = re.split(r'[.!?]+', text)
            relevant_sentences = [s.strip() for s in sentences if concept.lower() in s.lower()]
            
            if relevant_sentences:
                # Use the first relevant sentence as the back of the card
                back_text = relevant_sentences[0]
                front_text = f"What is {concept}?"
                
                flashcard = FlashcardData(
                    front=front_text,
                    back=back_text,
                    concept=concept,
                    difficulty="medium"
                )
                flashcards.append(flashcard)
        
        return flashcards


class AIContentGenerator:
    """Main service class that orchestrates all AI content generation"""
    
    def __init__(self):
        self.concept_extractor = ConceptExtractor()
        self.summary_generator = SummaryGenerator()
        self.quiz_generator = QuizGenerator()
        self.flashcard_generator = FlashcardGenerator()
    
    def generate_all_content(self, uploaded_content: UploadedContent) -> Dict[str, Any]:
        """
        Generate all AI content for uploaded content
        
        Args:
            uploaded_content: UploadedContent instance
            
        Returns:
            dict: Results of all content generation
        """
        results = {
            'success': True,
            'concepts': [],
            'summaries': {},
            'quizzes': [],
            'flashcards': [],
            'errors': []
        }
        
        text = uploaded_content.extracted_text
        if not text:
            results['success'] = False
            results['errors'].append("No extracted text available")
            return results
        
        try:
            # Extract key concepts
            logger.info(f"Extracting concepts for {uploaded_content.original_filename}")
            concepts = self.concept_extractor.extract_concepts(text)
            results['concepts'] = concepts
            
            # Update the uploaded content with concepts
            uploaded_content.key_concepts = concepts
            uploaded_content.save()
            
        except Exception as e:
            logger.error(f"Concept extraction failed: {str(e)}")
            results['errors'].append(f"Concept extraction failed: {str(e)}")
        
        # Generate summaries
        for summary_type in SummaryType:
            try:
                logger.info(f"Generating {summary_type.value} summary for {uploaded_content.original_filename}")
                summary_text = self.summary_generator.generate_summary(text, summary_type)
                
                # Save to database
                summary, created = GeneratedSummary.objects.get_or_create(
                    content=uploaded_content,
                    summary_type=summary_type.value,
                    defaults={'text': summary_text}
                )
                
                if not created:
                    summary.text = summary_text
                    summary.save()
                
                results['summaries'][summary_type.value] = summary_text
                
            except Exception as e:
                logger.error(f"Summary generation failed for {summary_type.value}: {str(e)}")
                results['errors'].append(f"Summary generation failed for {summary_type.value}: {str(e)}")
        
        # Generate quiz
        try:
            logger.info(f"Generating quiz for {uploaded_content.original_filename}")
            quiz_questions = self.quiz_generator.generate_quiz(text, num_questions=5)
            
            if quiz_questions:
                # Convert to JSON format for storage
                questions_json = []
                for q in quiz_questions:
                    questions_json.append({
                        'question': q.question,
                        'type': q.question_type,
                        'options': q.options,
                        'correct_answer': q.correct_answer,
                        'explanation': q.explanation,
                        'difficulty': q.difficulty
                    })
                
                # Save to database
                quiz = GeneratedQuiz.objects.create(
                    content=uploaded_content,
                    title=f"Quiz: {uploaded_content.original_filename}",
                    questions=questions_json,
                    difficulty_level='medium'
                )
                
                results['quizzes'] = questions_json
            
        except Exception as e:
            logger.error(f"Quiz generation failed: {str(e)}")
            results['errors'].append(f"Quiz generation failed: {str(e)}")
        
        # Generate flashcards
        try:
            logger.info(f"Generating flashcards for {uploaded_content.original_filename}")
            flashcard_data = self.flashcard_generator.generate_flashcards(text, num_cards=8)
            
            # Save to database
            for i, card_data in enumerate(flashcard_data):
                Flashcard.objects.create(
                    content=uploaded_content,
                    front_text=card_data.front,
                    back_text=card_data.back,
                    concept_tag=card_data.concept,
                    difficulty_level=card_data.difficulty,
                    order_index=i
                )
            
            results['flashcards'] = [
                {
                    'front': card.front,
                    'back': card.back,
                    'concept': card.concept,
                    'difficulty': card.difficulty
                }
                for card in flashcard_data
            ]
            
        except Exception as e:
            logger.error(f"Flashcard generation failed: {str(e)}")
            results['errors'].append(f"Flashcard generation failed: {str(e)}")
        
        # Determine overall success
        if results['errors']:
            results['success'] = len(results['errors']) < 3  # Allow some failures
        
        logger.info(f"AI content generation completed for {uploaded_content.original_filename}")
        return results


# Global instance
ai_content_generator = AIContentGenerator()