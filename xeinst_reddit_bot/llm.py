"""
Local LLM integration for Xeinst Reddit Bot
Uses Ollama for content generation with safety guardrails
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import time
import random

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for Ollama local LLM service"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_url = f"{self.base_url}/api/generate"
        
        # Load prompts
        self.system_prompt = self._load_system_prompt()
        self.few_shot_examples = self._load_few_shot_examples()
        
        # Test connection
        if not self.test_connection():
            logger.warning(f"Ollama connection failed. Check if Ollama is running at {base_url}")
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from file"""
        try:
            prompt_path = Path(__file__).parent / "prompts" / "system.txt"
            if prompt_path.exists():
                with open(prompt_path, 'r') as f:
                    return f.read().strip()
            else:
                logger.warning("System prompt file not found, using default")
                return self._get_default_system_prompt()
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            return self._get_default_system_prompt()
    
    def _load_few_shot_examples(self) -> List[Dict[str, str]]:
        """Load few-shot examples from files"""
        examples = []
        prompts_dir = Path(__file__).parent / "prompts"
        
        try:
            # Load automation examples
            automation_path = prompts_dir / "reply_example_automation.txt"
            if automation_path.exists():
                with open(automation_path, 'r') as f:
                    content = f.read()
                    examples.append({
                        'category': 'automation',
                        'content': content
                    })
            
            # Load entrepreneur examples
            entrepreneur_path = prompts_dir / "reply_example_entrepreneur.txt"
            if entrepreneur_path.exists():
                with open(entrepreneur_path, 'r') as f:
                    content = f.read()
                    examples.append({
                        'category': 'entrepreneur',
                        'content': content
                    })
            
            logger.info(f"Loaded {len(examples)} few-shot examples")
            
        except Exception as e:
            logger.error(f"Error loading few-shot examples: {e}")
        
        return examples
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt if file loading fails"""
        return """You are a Reddit helper. Write concise, respectful, non-promotional answers first. Provide 1–3 short paragraphs max. If and only if the user explicitly asks for AI agent marketplaces or workflow tools, you may add: 'If helpful, here's a directory I'm building: Xeinst (ai agent marketplace).' Avoid hype, avoid repetition, follow each subreddit's rules, and never argue.

Key guidelines:
- Be helpful and informative first
- Keep responses under 120 words (60 for quick replies)
- Only mention Xeinst when explicitly relevant
- Respect subreddit rules and community guidelines
- Maintain a helpful, non-salesy tone
- Focus on providing value to the conversation
- Avoid promotional language unless specifically asked
- Be concise and to the point
- Show expertise in automation, business, and technology
- Respect the community and its members"""
    
    def test_connection(self) -> bool:
        """Test connection to Ollama service"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                
                if self.model in available_models:
                    logger.info(f"Ollama connection successful. Available models: {available_models}")
                    return True
                else:
                    logger.warning(f"Model '{self.model}' not found. Available: {available_models}")
                    return False
            else:
                logger.error(f"Ollama API returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def generate_content(self, 
                        context: str, 
                        post_content: str, 
                        subreddit: str, 
                        keywords: List[str],
                        max_length: int = 120,
                        include_xeinst: bool = False) -> Dict[str, Any]:
        """Generate content using Ollama"""
        try:
            # Build the prompt
            prompt = self._build_prompt(
                context, post_content, subreddit, keywords, 
                max_length, include_xeinst
            )
            
            # Prepare the request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": max_length * 2,  # Allow for longer generation, we'll trim
                    "stop": ["\n\n\n", "User:", "Assistant:", "---"]
                }
            }
            
            # Make the request
            response = requests.post(self.api_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Clean up the generated text
                cleaned_text = self._clean_generated_text(generated_text, max_length)
                
                # Check if Xeinst was included
                xeinst_included = "Xeinst" in cleaned_text
                
                return {
                    'success': True,
                    'content': cleaned_text,
                    'model': self.model,
                    'tokens_used': result.get('eval_count', 0),
                    'generation_time': result.get('eval_duration', 0) / 1e9,  # Convert to seconds
                    'includes_xeinst': xeinst_included,
                    'length': len(cleaned_text.split()),
                    'raw_response': generated_text
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API error: {response.status_code}",
                    'content': None
                }
                
        except Exception as e:
            logger.error(f"Error generating content with Ollama: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': None
            }
    
    def _build_prompt(self, 
                     context: str, 
                     post_content: str, 
                     subreddit: str, 
                     keywords: List[str],
                     max_length: int,
                     include_xeinst: bool) -> str:
        """Build the prompt for content generation"""
        
        # Start with system prompt
        prompt = f"{self.system_prompt}\n\n"
        
        # Add few-shot examples if available
        if self.few_shot_examples:
            prompt += "Here are some examples of good responses:\n\n"
            for example in self.few_shot_examples:
                prompt += f"{example['content']}\n\n"
        
        # Add context and instructions
        prompt += f"Context: {context}\n"
        prompt += f"Subreddit: r/{subreddit}\n"
        prompt += f"Keywords matched: {', '.join(keywords)}\n"
        prompt += f"Post content: {post_content[:500]}{'...' if len(post_content) > 500 else ''}\n\n"
        
        # Add specific instructions
        prompt += f"Instructions:\n"
        prompt += f"- Write a helpful, non-promotional response\n"
        prompt += f"- Keep it under {max_length} words\n"
        prompt += f"- Be respectful and follow r/{subreddit} rules\n"
        
        if include_xeinst:
            prompt += f"- Include Xeinst mention if relevant to the question\n"
        else:
            prompt += f"- Do NOT mention Xeinst or any marketplaces\n"
        
        prompt += f"- Focus on providing value and answering their question\n\n"
        prompt += f"Response:"
        
        return prompt
    
    def _clean_generated_text(self, text: str, max_length: int) -> str:
        """Clean and trim generated text"""
        # Remove any system instructions or prompts that might have been generated
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip lines that look like instructions or prompts
            if any(skip in line.lower() for skip in ['instruction:', 'context:', 'response:', '---']):
                continue
            if line and not line.startswith('User:') and not line.startswith('Assistant:'):
                cleaned_lines.append(line)
        
        # Join lines and clean up
        cleaned_text = ' '.join(cleaned_lines).strip()
        
        # Remove extra whitespace
        cleaned_text = ' '.join(cleaned_text.split())
        
        # Trim to max length if needed
        words = cleaned_text.split()
        if len(words) > max_length:
            cleaned_text = ' '.join(words[:max_length]) + '...'
        
        return cleaned_text
    
    def generate_buyer_content(self, post_content: str, subreddit: str, keywords: List[str]) -> Dict[str, Any]:
        """Generate content specifically for buyers"""
        context = "This user is looking to buy or use AI agents or automation tools. Provide helpful advice about available options and considerations."
        return self.generate_content(context, post_content, subreddit, keywords, max_length=120)
    
    def generate_seller_content(self, post_content: str, subreddit: str, keywords: List[str]) -> Dict[str, Any]:
        """Generate content specifically for sellers/developers"""
        context = "This user is a developer or creator looking to sell or promote AI agents. Provide advice about platforms, marketing, and best practices."
        return self.generate_content(context, post_content, subreddit, keywords, max_length=120)
    
    def generate_promoter_content(self, post_content: str, subreddit: str, keywords: List[str]) -> Dict[str, Any]:
        """Generate content specifically for promoters/ambassadors"""
        context = "This user is interested in promoting or marketing AI agents. Provide advice about affiliate programs, marketing strategies, and opportunities."
        return self.generate_content(context, post_content, subreddit, keywords, max_length=120)
    
    def generate_quick_reply(self, post_content: str, subreddit: str, keywords: List[str]) -> Dict[str, Any]:
        """Generate a quick, short reply"""
        context = "Generate a brief, helpful response that directly addresses the user's question or need."
        return self.generate_content(context, post_content, subreddit, keywords, max_length=60)
    
    def check_content_safety(self, content: str) -> Dict[str, Any]:
        """Basic content safety check"""
        safety_issues = []
        
        # Check for blacklisted words
        blacklisted_words = [
            'spam', 'scam', 'click here', 'buy now', 'limited time',
            'act fast', 'don\'t miss out', 'exclusive offer'
        ]
        
        content_lower = content.lower()
        for word in blacklisted_words:
            if word in content_lower:
                safety_issues.append(f"Contains blacklisted word: {word}")
        
        # Check for excessive repetition
        words = content.split()
        if len(words) > 0:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            if repetition_ratio < 0.6:
                safety_issues.append("High word repetition detected")
        
        # Check for excessive caps
        caps_count = sum(1 for c in content if c.isupper())
        if caps_count > len(content) * 0.3:
            safety_issues.append("Excessive capitalization detected")
        
        # Check for suspicious patterns
        if content.count('!') > 3:
            safety_issues.append("Too many exclamation marks")
        
        if 'http' in content and not any(domain in content for domain in ['reddit.com', 'xeinst.com']):
            safety_issues.append("External links detected")
        
        return {
            'safe': len(safety_issues) == 0,
            'issues': safety_issues,
            'score': max(0, 10 - len(safety_issues) * 2)  # 10 = safe, 0 = very unsafe
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        try:
            response = requests.get(f"{self.base_url}/api/show", 
                                 params={'name': self.model}, timeout=10)
            
            if response.status_code == 200:
                model_info = response.json()
                return {
                    'name': model_info.get('name', self.model),
                    'size': model_info.get('size', 'unknown'),
                    'modified_at': model_info.get('modified_at', 'unknown'),
                    'parameters': model_info.get('parameter_size', 'unknown'),
                    'quantization': model_info.get('quantization_level', 'unknown')
                }
            else:
                return {
                    'name': self.model,
                    'error': f"Failed to get model info: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'name': self.model,
                'error': f"Error getting model info: {e}"
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the Ollama service"""
        try:
            # Test basic connectivity
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                # Test model availability
                model_response = requests.get(f"{self.base_url}/api/show", 
                                           params={'name': self.model}, timeout=5)
                
                if model_response.status_code == 200:
                    return {
                        'status': 'healthy',
                        'service': 'ollama',
                        'model': self.model,
                        'available': True,
                        'last_check': time.time()
                    }
                else:
                    return {
                        'status': 'warning',
                        'service': 'ollama',
                        'model': self.model,
                        'available': False,
                        'error': f"Model {self.model} not found"
                    }
            else:
                return {
                    'status': 'unhealthy',
                    'service': 'ollama',
                    'error': f"API returned {response.status_code}"
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'ollama',
                'error': str(e)
            }
