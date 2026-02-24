"""
Ollama Client for AI Generation
Handles all communication with Ollama API
"""

import requests
import time
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from config.settings import settings
from ai.exceptions import (
    OllamaConnectionError,
    ModelNotFoundError,
    GenerationTimeoutError,
    ContextLengthExceededError,
    GenerationError
)
from utils.logger import LoggerMixin


class OllamaClient(LoggerMixin):
    """
    Client for interacting with Ollama API
    ENHANCED: Streaming support for real-time feedback
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize Ollama client"""
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.current_model = settings.DEFAULT_MODEL
        
        # Use appropriate timeout based on settings
        self.timeout = settings.OLLAMA_TIMEOUT
        self.connection_timeout = settings.OLLAMA_CONNECTION_TIMEOUT
        self.read_timeout = settings.OLLAMA_READ_TIMEOUT
        
        # Metrics tracking
        self.total_requests = 0
        self.total_tokens = 0
        self.total_time = 0.0
        
        self.logger.info(f"OllamaClient initialized - timeouts: connection={self.connection_timeout}s, read={self.read_timeout}s")
    
    # ========================================================================
    # CONNECTION & HEALTH
    # ========================================================================
    
    def test_connection(self) -> bool:
        """
        Verify Ollama server is accessible
        
        Returns:
            True if connection successful
            
        Raises:
            OllamaConnectionError: If connection fails
        """
        try:
            self.logger.info("Testing Ollama connection...")
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.connection_timeout
            )
            
            if response.status_code == 200:
                self.logger.info("✓ Ollama connection successful")
                return True
            else:
                raise OllamaConnectionError(
                    f"Ollama server returned status code {response.status_code}"
                )
                
        except requests.Timeout:
            self.logger.error("✗ Ollama connection timed out")
            raise OllamaConnectionError("Connection to Ollama timed out - is Ollama running?")
        except requests.ConnectionError as e:
            self.logger.error(f"✗ Cannot connect to Ollama: {e}")
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url} - is Ollama running?")
        except requests.RequestException as e:
            self.logger.error(f"✗ Ollama connection test failed: {e}")
            raise OllamaConnectionError(f"Failed to connect to Ollama: {e}")
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """Get list of installed models"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.connection_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                self.logger.info(f"Found {len(models)} available models")
                return models
            else:
                raise OllamaConnectionError(
                    f"Failed to list models: status {response.status_code}"
                )
                
        except requests.RequestException as e:
            self.logger.error(f"Failed to list models: {e}")
            raise OllamaConnectionError(f"Failed to list models: {e}")
    
    def verify_model(self, model_name: str) -> bool:
        """Check if a specific model is installed"""
        try:
            models = self.list_available_models()
            model_names = [m['name'] for m in models]
            exists = model_name in model_names
            
            if exists:
                self.logger.info(f"✓ Model '{model_name}' is available")
            else:
                self.logger.warning(f"✗ Model '{model_name}' not found. Available: {model_names}")
            
            return exists
            
        except OllamaConnectionError:
            return False
    
    # ========================================================================
    # STREAMING GENERATION (NEW - PRIMARY METHOD)
    # ========================================================================
    
    def generate_streaming(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        timeout: Optional[int] = None
    ) -> str:
        """
        Generate text with STREAMING for real-time progress
        
        Args:
            prompt: Input prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            system: System prompt
            progress_callback: Function called with (chunk, word_count) for each token
            timeout: Custom timeout in seconds
            
        Returns:
            Complete generated text
            
        Raises:
            ModelNotFoundError: If model not available
            GenerationTimeoutError: If generation times out
            GenerationError: If generation fails
        """
        model = model or self.current_model
        temperature = temperature or settings.DEFAULT_TEMPERATURE
        max_tokens = max_tokens or settings.DEFAULT_MAX_TOKENS
        timeout = timeout or self.read_timeout
        
        # Verify model exists
        if not self.verify_model(model):
            raise ModelNotFoundError(f"Model '{model}' is not available. Run 'ollama pull {model}' to download it.")
        
        self.logger.info(f"🚀 Starting STREAMING generation with '{model}' (timeout: {timeout}s)...")
        start_time = time.time()
        
        try:
            # Prepare request payload
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': True,  # CRITICAL: Enable streaming
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }
            
            if system:
                payload['system'] = system
            
            self.logger.info(f"📡 Sending request to Ollama API...")
            
            # Make streaming request with separate timeouts
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=(self.connection_timeout, timeout)  # (connect, read) timeouts
            )
            
            if response.status_code != 200:
                error_text = response.text[:500]
                self.logger.error(f"❌ Generation failed: {response.status_code} - {error_text}")
                raise GenerationError(
                    f"Generation failed with status {response.status_code}: {error_text}"
                )
            
            self.logger.info("✓ Connected to Ollama, streaming response...")
            
            full_text = ""
            word_count = 0
            last_callback_time = time.time()
            callback_interval = 0.1  # Update UI every 100ms
            
            # Process stream line by line
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        data = json.loads(line)
                        chunk = data.get('response', '')
                        
                        if chunk:
                            full_text += chunk
                            
                            # Update word count
                            if ' ' in chunk or '\n' in chunk:
                                word_count = len(full_text.split())
                            
                            # Call progress callback (throttled to avoid UI spam)
                            current_time = time.time()
                            if progress_callback and (current_time - last_callback_time) >= callback_interval:
                                progress_callback(chunk, word_count)
                                last_callback_time = current_time
                        
                        # Check if done
                        if data.get('done', False):
                            self.logger.info("✓ Streaming complete (done flag received)")
                            
                            # Final callback with complete text
                            if progress_callback:
                                progress_callback("", word_count)
                            
                            break
                            
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse JSON line: {e}")
                        continue
                    except Exception as e:
                        self.logger.error(f"Error processing stream: {e}")
                        continue
            
            generation_time = time.time() - start_time
            
            # Update metrics
            self.total_requests += 1
            self.total_time += generation_time
            self.total_tokens += word_count
            
            self.logger.info(
                f"✅ Generation complete in {generation_time:.1f}s "
                f"(~{word_count} words, ~{word_count*1.3:.0f} tokens)"
            )
            
            return full_text
            
        except requests.Timeout:
            elapsed = time.time() - start_time
            self.logger.error(f"❌ Generation timed out after {elapsed:.1f}s (limit: {timeout}s)")
            raise GenerationTimeoutError(
                f"Generation exceeded timeout of {timeout}s. Try reducing word count or switching to a faster model."
            )
        except requests.ConnectionError as e:
            self.logger.error(f"❌ Connection error during generation: {e}")
            raise GenerationError(f"Lost connection to Ollama during generation: {e}")
        except requests.RequestException as e:
            self.logger.error(f"❌ Request error: {e}")
            raise GenerationError(f"Generation request failed: {e}")
        except Exception as e:
            self.logger.error(f"❌ Unexpected error during generation: {e}")
            raise GenerationError(f"Unexpected error: {e}")
    
    # ========================================================================
    # NON-STREAMING GENERATION (FALLBACK)
    # ========================================================================
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> str:
        """
        Generate text WITHOUT streaming (fallback method)
        
        NOTE: Prefer generate_streaming() for better user experience
        """
        model = model or self.current_model
        temperature = temperature or settings.DEFAULT_TEMPERATURE
        max_tokens = max_tokens or settings.DEFAULT_MAX_TOKENS
        timeout = timeout or self.read_timeout
        
        # Verify model exists
        if not self.verify_model(model):
            raise ModelNotFoundError(f"Model '{model}' is not available")
        
        self.logger.info(f"Generating with model '{model}' (no streaming)...")
        start_time = time.time()
        
        try:
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }
            
            if system:
                payload['system'] = system
            
            # Make request with timeout
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=(self.connection_timeout, timeout)
            )
            
            if response.status_code == 200:
                data = response.json()
                generated_text = data.get('response', '')
                
                generation_time = time.time() - start_time
                self.total_requests += 1
                self.total_time += generation_time
                
                tokens = len(generated_text.split())
                self.total_tokens += tokens
                
                self.logger.info(f"Generation complete in {generation_time:.2f}s (~{tokens} tokens)")
                
                return generated_text
            else:
                raise GenerationError(
                    f"Generation failed with status {response.status_code}: {response.text}"
                )
                
        except requests.Timeout:
            raise GenerationTimeoutError(f"Generation exceeded timeout of {timeout}s")
        except requests.RequestException as e:
            raise GenerationError(f"Generation request failed: {e}")
    
    # ========================================================================
    # RETRY LOGIC
    # ========================================================================
    
    def generate_with_retry(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_retries: Optional[int] = None,
        backoff_factor: float = 2.0,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> str:
        """
        Generate with automatic retry on failure
        Uses STREAMING by default
        """
        max_retries = max_retries or settings.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                return self.generate_streaming(
                    prompt=prompt,
                    model=model,
                    progress_callback=progress_callback
                )
                
            except (GenerationError, GenerationTimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    self.logger.warning(
                        f"Generation attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All {max_retries} generation attempts failed")
                    raise GenerationError(f"Generation failed after {max_retries} attempts: {e}")
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def get_current_model(self) -> str:
        """
        Get name of currently active model
        
        Returns:
            Current model name
        """
        return self.current_model
    
    def switch_model(self, new_model: str) -> bool:
        """
        Change active model
        
        Args:
            new_model: Name of model to switch to
            
        Returns:
            True if successful, False otherwise
        """
        if self.verify_model(new_model):
            old_model = self.current_model
            self.current_model = new_model
            self.logger.info(f"Switched model from '{old_model}' to '{new_model}'")
            return True
        else:
            self.logger.error(f"Cannot switch to unavailable model '{new_model}'")
            return False
    
    def estimate_generation_time(self, word_count: int, model: str = "llama3.1:8b") -> float:
        """
        Estimate generation time based on word count
        
        Args:
            word_count: Target word count
            model: Model name
            
        Returns:
            Estimated time in seconds
        """
        # Rough estimates (tokens/second)
        speeds = {
            "llama3.1:8b": 20,  # ~20 tokens/sec on average hardware
            "llama3.1:70b": 5,  # ~5 tokens/sec (much slower)
            "mistral-nemo:12b": 25,  # ~25 tokens/sec (faster than 8b)
        }
        
        tokens_per_sec = speeds.get(model, 15)
        estimated_tokens = word_count * 1.3  # words to tokens
        
        estimated_time = estimated_tokens / tokens_per_sec
        
        # Add 20% buffer for context processing
        return estimated_time * 1.2
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client usage metrics"""
        avg_time = self.total_time / self.total_requests if self.total_requests > 0 else 0
        
        return {
            'total_requests': self.total_requests,
            'total_tokens': self.total_tokens,
            'total_time': self.total_time,
            'average_generation_time': avg_time,
            'current_model': self.current_model
        }
    
    def reset_metrics(self):
        """Reset all metrics counters"""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_time = 0.0
        self.logger.info("Metrics reset")


# Global Ollama client instance
ollama_client = OllamaClient()