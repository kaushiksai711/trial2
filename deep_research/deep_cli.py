import os
import requests
import json
import time
import concurrent.futures
from urllib.parse import quote, urlparse
from datetime import datetime
import re
from typing import List, Dict, Any, Optional
import functools
import logging

logging.basicConfig(filename='raw/research_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')
# MeTTa integration imports
try:
    from hyperon import MeTTa, OperationAtom, ValueAtom
    METTA_AVAILABLE = True
    logging.info("✅ MeTTa library imported successfully")
except ImportError:
    logging.info("⚠️ MeTTa not available - continuing without MeTTa integration")
    METTA_AVAILABLE = False

# Global variable to store research context for MeTTa
METTA_RESEARCH_CONTEXT = {}

# Retry decorator for extraction
def retry(max_attempts=3, delay=2):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    logging.info(f"Retry {attempt + 1}/{max_attempts} for {args[0] if args else 'unknown'}: {e}")
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

# ===============================
# Step 1: Enhanced API Wrappers
# ===============================
class AdvancedAPIWrapper:
    def __init__(self):
        serper_key = os.getenv("SERPER_API_KEY", "135dd2e36474b4e2bf13bb52f155af1acdb9e89a")
        jina_key = os.getenv("JINA_API_KEY", "jina_2ef7173d7a0a42868bee6ef38bfc9b5f_7v9lpo9Nj-WCLe-kUvYkRf-F3B9")
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "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")

        self.serper_key = serper_key
        self.jina_key = jina_key
        self.openrouter_key = openrouter_key

        # Set environment variables
        os.environ["SERPER_API_KEY"] = self.serper_key
        os.environ["JINA_API_KEY"] = self.jina_key
        os.environ["OPENROUTER_API_KEY"] = self.openrouter_key

        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.session = session

    def enhanced_serper_search(self, query: str, num_results: int = 10) -> list:
        """Enhanced search that gets multiple results with metadata"""
        try:
            url = "https://google.serper.dev/search"
            headers = {"X-API-KEY": self.serper_key, "Content-Type": "application/json"}

            payload = {
                "q": query,
                "num": num_results,
                "gl": "us",
                "hl": "en",
                "type": "search"
            }

            response = self.session.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

            results = []

            organic_results = data.get("organic", [])[:num_results]
            for item in organic_results:
                result = {
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'position': item.get('position', 0),
                    'date': item.get('date', ''),
                    'source': 'organic'
                }
                if result['link']:
                    results.append(result)

            news_results = data.get("news", [])[:3]
            for item in news_results:
                result = {
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'date': item.get('date', ''),
                    'source': 'news'
                }
                if result['link']:
                    results.append(result)

            if 'knowledgeGraph' in data:
                kg = data['knowledgeGraph']
                if kg.get('website'):
                    result = {
                        'title': f"Knowledge: {kg.get('title', query)}",
                        'link': kg['website'],
                        'snippet': kg.get('description', ''),
                        'source': 'knowledge_graph'
                    }
                    results.append(result)

            return results[:num_results]

        except Exception as e:
            logging.info(f"⚠️ Serper search error: {e}")
            return []

    @retry(max_attempts=3, delay=1)
    def _extract_single_url(self, url: str) -> tuple:
        """Extract content from a single URL with retry"""
        try:
            api_url = f"https://r.jina.ai/{url}"
            response = self.session.get(api_url, timeout=60)  # Increased timeout
            response.raise_for_status()

            content = response.text
            cleaned_content = self._clean_content(content)

            # No length limit - keep full content
            return (url, cleaned_content)

        except Exception as e:
            error_msg = f"Error extracting content: {str(e)[:100]}"
            return (url, error_msg)

    def batch_content_extraction(self, urls: List[str], max_workers: int = 8) -> Dict[str, str]:
        """Extract content from multiple URLs concurrently with improved handling"""
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self._extract_single_url, url): url for url in urls}

            for future in concurrent.futures.as_completed(future_to_url):
                # Removed timeout to allow full completion
                try:
                    result = future.result()
                    url, content = result
                    results[url] = content
                except Exception as e:
                    url = future_to_url[future]
                    results[url] = f"Timeout or error: {str(e)[:100]}"

        return results

    def _clean_content(self, content: str) -> str:
        """Clean extracted content - enhanced for Jina metadata"""
        # Remove Jina-specific metadata
        jina_patterns = [
            r'^Title:.*?\n',
            r'^URL Source:.*?\n',
            r'^URL:.*?\n',
            r'^Published Time:.*?\n',
            r'^Author:.*?\n',
            r'^Markdown Content:.*?\n',
            r'^Content:.*?\n'
        ]
        for pattern in jina_patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)

        # Remove markdown links and images
        content = re.sub(r'\[.*?\]\(.*?\)', '', content)
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)

        # Remove common web artifacts
        cleaned = re.sub(r'\s+', ' ', content)

        patterns_to_remove = [
            r'Cookie.*?Accept',
            r'Navigation.*?Menu',
            r'Subscribe.*?Newsletter',
            r'Follow us on.*?social',
            r'Share.*?Facebook.*?Twitter',
            r'Skip to.*?content',
            r'Table of Contents',
            r'Related Articles?',
            r'Advertisement',
            r'Ad\s*$',
            r'Sign up.*?free',
            r'Log in.*?account',
        ]

        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    def intelligent_chat(self, content_data: Dict[str, Any], question: str, model: str = "openai/gpt-4o-mini") -> Dict[str, Any]:
        """Enhanced chat with intelligent content synthesis and comprehensive source attribution - MAXIMUM content generation"""
        try:
            sources_summary = []
            source_mapping = {}

            results_data = content_data['results']
            source_index = 1

            for url, result in results_data.items():
                if not result['content'].startswith('Error'):
                    domain = urlparse(url).netloc
                    # Use full content for LLM - no preview limit
                    content_full = result['content']

                    summary_item = f"=== SOURCE {source_index} ===\nDomain: {domain}\nURL: {url}\nTitle: {result['title']}\nContent: {content_full}"

                    sources_summary.append(summary_item)

                    source_mapping[source_index] = {
                        'url': url,
                        'domain': domain,
                        'title': result['title']
                    }
                    source_index += 1

            system_prompt = """You are an expert research analyst with a STRICT requirement to cite ALL sources for EVERY claim you make.

CRITICAL CITATION RULES (YOU MUST FOLLOW THESE):
1. For EVERY factual statement, data point, or claim, you MUST include [Source X] citation
2. Use format: [Source X] where X is the source number (1, 2, 3, etc.)
3. You can cite multiple sources like: [Source 1, 3] or [Source 2, 4, 5]
4. NEVER make a claim without citing the source it came from
5. If information appears in multiple sources, cite all of them
6. For contradicting information, cite the specific sources and note the contradiction
7. At the end, include a comprehensive "SOURCES REFERENCED" section listing all sources you cited

RESPONSE STRUCTURE REQUIREMENTS - GENERATE COMPREHENSIVE CONTENT:
1. Start with a detailed executive summary (2-3 paragraphs) citing key sources
2. Create a comprehensive table of contents
3. Provide DETAILED sections with multiple subsections for each main topic
4. Under each heading, provide extensive information with citations for EVERY claim
5. Include specific examples, case studies, and evidence with their source citations
6. Add detailed analysis, implications, and future considerations
7. Include comparative analysis between sources where applicable
8. Provide extensive background context and historical perspective
9. Add methodology discussions and technical details where relevant
10. Include limitations, challenges, and counterarguments with citations
11. End with detailed conclusions and recommendations
12. Finish with comprehensive "SOURCES REFERENCED" section

CONTENT LENGTH REQUIREMENT: Generate a comprehensive research report of AT LEAST 15,000-20,000 words. Be thorough, detailed, and exhaustive in your analysis. Use ALL available source content to create the most comprehensive response possible.

Remember: NO STATEMENT WITHOUT CITATION. Every piece of information must be traceable to its source. Be extremely detailed and comprehensive."""

            user_prompt = f"""Research Question: {question}

AVAILABLE SOURCES FOR ANALYSIS:
{chr(10).join(sources_summary)}

SOURCE REFERENCE MAP:
{chr(10).join([f"Source {idx}: {info['domain']} - {info['title']} ({info['url']})" for idx, info in source_mapping.items()])}

RESEARCH CONTEXT:
- Total sources analyzed: {len(source_mapping)}
- Search queries used: {content_data.get('search_queries', [])}
- Processing completed successfully for {len([r for r in content_data['results'].values() if not r['content'].startswith('Error')])} sources

TASK: Provide a comprehensive, exhaustive research analysis answering the research question. Generate AT LEAST 15,000-20,000 words of detailed content. You MUST cite sources for every claim using [Source X] format. Be extremely thorough, detailed, and comprehensive. Use ALL the content provided in each source to derive extensive insights. Create multiple sections, subsections, detailed examples, case studies, comparative analysis, technical details, historical context, implications, and recommendations. This should be a complete research report."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
            }

            # CRITICAL CHANGES FOR LONGER CONTENT:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.1,  # Lower for more focused content
                "max_tokens": 16000,  # INCREASED significantly for longer responses
                "top_p": 0.9,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }

            response = self.session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=300  # Increased timeout for longer generation
            )
            response.raise_for_status()

            data = response.json()
            result = data["choices"][0]["message"]["content"]

            enhanced_result = {
                'analysis': result,
                'source_mapping': source_mapping
            }

            return enhanced_result

        except Exception as e:
            error_result = {
                'analysis': f"Analysis error: {str(e)}",
                'source_mapping': {}
            }
            return error_result

    # ADDITIONAL METHOD FOR MULTI-PART GENERATION (Alternative approach)
    def generate_comprehensive_multi_part_analysis(self, question: str, research_data: Dict[str, Any], model: str = "openai/gpt-4o-mini") -> Dict[str, Any]:
        """Generate analysis in multiple parts to exceed token limits"""

        # Part 1: Executive Summary and Introduction
        part1_prompt = f"""Generate a comprehensive executive summary and introduction for the research question: {question}

        Use the provided sources and create:
        1. Detailed executive summary (1000+ words)
        2. Comprehensive introduction with background (1000+ words)
        3. Methodology and approach (500+ words)
        4. Table of contents for the full report

        Cite ALL sources using [Source X] format."""

        # Part 2: Main Analysis
        part2_prompt = f"""Generate the main analysis section for: {question}

        Create detailed sections covering:
        1. Current state analysis (2000+ words)
        2. Key findings and insights (2000+ words)
        3. Comparative analysis between sources (1500+ words)
        4. Technical details and specifications (1500+ words)

        Cite ALL sources using [Source X] format."""

        # Part 3: Implications and Conclusions
        part3_prompt = f"""Generate conclusions and implications for: {question}

        Include:
        1. Detailed implications and impact analysis (1500+ words)
        2. Future trends and predictions (1500+ words)
        3. Recommendations and best practices (1500+ words)
        4. Limitations and challenges (1000+ words)
        5. Comprehensive conclusions (1000+ words)
        6. Complete sources referenced section

        Cite ALL sources using [Source X] format."""

        # Generate each part separately
        parts = []
        for i, prompt in enumerate([part1_prompt, part2_prompt, part3_prompt], 1):
            part_result = self._generate_single_part(prompt, research_data, model)
            parts.append(f"=== PART {i} ===\n{part_result}")

        # Combine all parts
        combined_analysis = "\n\n".join(parts)

        return {
            'analysis': combined_analysis,
            'source_mapping': self._build_source_mapping(research_data)
        }

    def _generate_single_part(self, prompt: str, research_data: Dict[str, Any], model: str) -> str:
        """Generate a single part of the analysis"""
        try:
            # Build sources for this part
            sources_content = self._build_sources_content(research_data)

            full_prompt = f"{prompt}\n\nSOURCES:\n{sources_content}"

            messages = [
                {"role": "system", "content": "You are an expert research analyst. Generate detailed, comprehensive content with proper source citations."},
                {"role": "user", "content": full_prompt}
            ]

            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 16000,  # Maximum tokens per part
            }

            response = self.session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.openrouter_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=300
            )

            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except Exception as e:
            return f"Error generating part: {str(e)}"

    def _build_sources_content(self, research_data: Dict[str, Any]) -> str:
        """Build formatted sources content"""
        sources_summary = []
        source_index = 1

        for url, result in research_data['results'].items():
            if not result['content'].startswith('Error'):
                summary_item = f"=== SOURCE {source_index} ===\nURL: {url}\nTitle: {result['title']}\nContent: {result['content']}"
                sources_summary.append(summary_item)
                source_index += 1

        return "\n\n".join(sources_summary)

    def _build_source_mapping(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build source mapping for citations"""
        source_mapping = {}
        source_index = 1

        for url, result in research_data['results'].items():
            if not result['content'].startswith('Error'):
                source_mapping[source_index] = {
                    'url': url,
                    'domain': urlparse(url).netloc,
                    'title': result['title']
                }
                source_index += 1

        return source_mapping

# ===============================
# Step 1.5: Fixed MeTTa Integration Functions
# ===============================

@retry(max_attempts=3, delay=1)
def _extract_single_url_metta(url: str) -> tuple:
    """Shared extraction function for MeTTa with retry and increased timeout"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        api_url = f"https://r.jina.ai/{url}"
        response = session.get(api_url, timeout=60)  # Increased timeout
        response.raise_for_status()

        content = response.text

        # Enhanced cleaning for Jina metadata and artifacts
        # Remove Jina-specific metadata
        jina_patterns = [
            r'^Title:.*?\n',
            r'^URL Source:.*?\n',
            r'^URL:.*?\n',
            r'^Published Time:.*?\n',
            r'^Author:.*?\n',
            r'^Markdown Content:.*?\n',
            r'^Content:.*?\n'
        ]
        for pattern in jina_patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)

        # Remove markdown links and images
        content = re.sub(r'\[.*?\]\(.*?\)', '', content)
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)

        # Remove common web artifacts
        cleaned = re.sub(r'\s+', ' ', content)

        patterns_to_remove = [
            r'Cookie.*?Accept',
            r'Navigation.*?Menu',
            r'Subscribe.*?Newsletter',
            r'Follow us on.*?social',
            r'Share.*?Facebook.*?Twitter',
            r'Skip to.*?content',
            r'Table of Contents',
            r'Related Articles?',
            r'Advertisement',
            r'Ad\s*$',
            r'Sign up.*?free',
            r'Log in.*?account',
        ]

        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        cleaned_content = cleaned.strip()

        # No length limit - keep full content

        return (url, cleaned_content)

    except Exception as e:
        error_msg = f"Error extracting content: {str(e)[:100]}"
        return (url, error_msg)

def enhanced_serper_search_metta(query, num_results: int = 10):
    """Enhanced MeTTa-compatible serper search that returns structured data, now dynamic num_results"""
    global METTA_RESEARCH_CONTEXT

    try:
        serper_key = os.getenv("SERPER_API_KEY", "135dd2e36474b4e2bf13bb52f155af1acdb9e89a")
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}

        # Extract clean query from MeTTa atom
        if hasattr(query, 'get_object'):
            clean_query = str(query.get_object())
        else:
            clean_query = str(query)

        clean_query = clean_query.strip().strip('"').strip("'")
        logging.info(f"🔍 Enhanced MeTTa Serper search for: '{clean_query}' (num_results: {num_results})")

        payload = {
            "q": clean_query,
            "num": num_results,
            "gl": "us",
            "hl": "en",
            "type": "search"
        }

        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        response = session.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        organic_results = data.get("organic", [])

        if organic_results:
            # Store multiple results in context for better selection
            search_results = []
            for i, result in enumerate(organic_results[:num_results]):
                url_result = result.get('link', '')
                title = result.get('title', 'Unknown Title')
                snippet = result.get('snippet', '')

                if url_result:
                    search_results.append({
                        'url': url_result,
                        'title': title,
                        'snippet': snippet,
                        'position': i + 1
                    })

            # Store in global context for content extraction
            METTA_RESEARCH_CONTEXT[clean_query] = {
                'search_results': search_results,
                'timestamp': datetime.now().isoformat()
            }

            # Return the best URL (first result)
            best_result = search_results[0]
            logging.info(f"✅ Found {len(search_results)} results, returning best: {best_result['url']}")
            logging.info(f"   Title: {best_result['title']}")

            return ValueAtom(best_result['url'])

        logging.info("⚠️ No results found")
        return ValueAtom("")

    except Exception as e:
        logging.info(f"❌ Enhanced MeTTa Serper search error: {e}")
        return ValueAtom(f"Error: {str(e)}")

def enhanced_jina_reader_metta(url_atom):
    """Enhanced MeTTa-compatible jina reader using shared extraction"""
    global METTA_RESEARCH_CONTEXT

    try:
        # Extract URL from MeTTa atom
        if hasattr(url_atom, 'get_object'):
            clean_url = str(url_atom.get_object())
        else:
            clean_url = str(url_atom)

        clean_url = clean_url.strip().strip('"').strip("'")
        logging.info(f"📖 Enhanced MeTTa Jina reader for: {clean_url}")

        if not clean_url or not clean_url.startswith('http'):
            logging.info(f"❌ Invalid URL: {clean_url}")
            return ValueAtom("Error: Invalid URL provided")

        # Use shared extraction function
        url_result, content = _extract_single_url_metta(clean_url)

        if content.startswith('Error'):
            return ValueAtom(content)

        logging.info(f"✅ Content extracted: {len(content)} characters")

        # Store in context if available
        source_info = None
        for query, context in METTA_RESEARCH_CONTEXT.items():
            for result in context.get('search_results', []):
                if result['url'] == clean_url:
                    source_info = result
                    break
            if source_info:
                break

        if source_info:
            source_info['extracted_content'] = content
            source_info['extraction_success'] = True

        return ValueAtom(content)

    except Exception as e:
        error_msg = f"Error reading content from {clean_url}: {str(e)[:200]}"
        logging.info(f"❌ Enhanced MeTTa Jina error: {error_msg}")
        return ValueAtom(error_msg)

def multi_source_metta_research(query, num_sources: int = 5):
    """Enhanced MeTTa research that processes multiple sources concurrently, now dynamic num_sources"""
    global METTA_RESEARCH_CONTEXT

    try:
        # Extract clean query
        if hasattr(query, 'get_object'):
            clean_query = str(query.get_object())
        else:
            clean_query = str(query)

        clean_query = clean_query.strip().strip('"').strip("'")
        logging.info(f"🔍 Multi-source MeTTa research for: '{clean_query}' (num_sources: {num_sources})")

        # First, search for sources with dynamic num_results
        search_result = enhanced_serper_search_metta(ValueAtom(clean_query), num_results=num_sources * 2)  # Search more to get quality

        if not search_result or str(search_result.get_object()).startswith('Error'):
            return ValueAtom("Error: Could not find sources")

        # Get context with multiple sources
        context = METTA_RESEARCH_CONTEXT.get(clean_query, {})
        search_results = context.get('search_results', [])

        if not search_results:
            return ValueAtom("Error: No search results found")

        # Extract content from top num_sources sources CONCURRENTLY
        unique_urls = [source['url'] for source in search_results[:num_sources]]
        content_results = {}

        def extract_single(url):
            return _extract_single_url_metta(url)

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(unique_urls))) as executor:  # Increased max_workers
            future_to_url = {executor.submit(extract_single, url): url for url in unique_urls}

            for future in concurrent.futures.as_completed(future_to_url):
                # Removed timeout to allow full completion
                try:
                    url_result, content = future.result()
                    content_results[url_result] = content
                except Exception as e:
                    url = future_to_url[future]
                    content_results[url] = f"Timeout or error: {str(e)[:100]}"

        # Build combined content and set metadata
        successful_extractions = 0

        for source in search_results[:num_sources]:
            url = source['url']
            content = content_results.get(url, "Content not available")

            if not content.startswith('Error') and len(content) > 200:
                source['extracted_content'] = content
                source['extraction_success'] = True
                successful_extractions += 1
            else:
                source['extracted_content'] = content
                source['extraction_success'] = False

        METTA_RESEARCH_CONTEXT[clean_query]['successful_extractions'] = successful_extractions
        METTA_RESEARCH_CONTEXT[clean_query]['requested_sources'] = num_sources

        logging.info(f"✅ Multi-source research completed: {successful_extractions} successful extractions out of {len(search_results[:num_sources])}")
        return ValueAtom("Success")  # Signal success, data is in context

    except Exception as e:
        error_msg = f"Multi-source MeTTa research error: {str(e)}"
        logging.info(f"❌ {error_msg}")
        return ValueAtom(error_msg)

def setup_metta_integration():
    """Setup enhanced MeTTa integration with better functions"""
    if not METTA_AVAILABLE:
        logging.info("⚠️ MeTTa not available")
        return None

    try:
        logging.info("🧠 Setting up enhanced MeTTa integration...")
        metta = MeTTa()

        # Create enhanced operation atoms (note: functions now take extra params, but MeTTa calls need adjustment)
        # For simplicity, we'll handle params in the function calls below
        enhanced_serper_atom = OperationAtom("enhanced-serper-search", lambda q: enhanced_serper_search_metta(q, 10))  # Default 10
        enhanced_jina_atom = OperationAtom("enhanced-jina-reader", enhanced_jina_reader_metta)
        multi_source_atom = OperationAtom("multi-source-research", lambda q: multi_source_metta_research(q, 5))  # Default 5, overridden in run

        # Register atoms with MeTTa
        metta.register_atom("enhanced-serper-search", enhanced_serper_atom)
        metta.register_atom("enhanced-jina-reader", enhanced_jina_atom)
        metta.register_atom("multi-source-research", multi_source_atom)

        # Keep backward compatibility
        metta.register_atom("serper-search", enhanced_serper_atom)
        metta.register_atom("jina-reader", enhanced_jina_atom)

        logging.info("✅ Enhanced MeTTa atoms registered successfully")
        return metta

    except Exception as e:
        logging.info(f"❌ Enhanced MeTTa setup error: {e}")
        import traceback
        logging.info(traceback.format_exc())
        return None

def run_enhanced_metta_research(query: str, num_sources: int = 5, metta_instance=None):
    """Enhanced MeTTa-based research with better result processing, now dynamic num_sources"""
    global METTA_RESEARCH_CONTEXT

    if not METTA_AVAILABLE or metta_instance is None:
        return "MeTTa not available or not initialized"

    try:
        logging.info(f"🧠 Starting enhanced MeTTa research for: '{query}' (num_sources: {num_sources})")

        # Clean the query for MeTTa
        clean_query = query.strip().replace('"', '\\"')

        # Use the multi-source research function with dynamic num_sources
        metta_script = f'!(multi-source-research "{clean_query}")'  # Params handled internally now via global or adjustment

        # Temporarily override the operation to pass num_sources
        original_func = multi_source_metta_research
        multi_source_metta_research_dynamic = lambda q: original_func(q, num_sources)
        dynamic_atom = OperationAtom("multi-source-research", multi_source_metta_research_dynamic)
        metta_instance.register_atom("multi-source-research", dynamic_atom)

        logging.info(f"🔧 Executing enhanced MeTTa script: {metta_script}")

        result = metta_instance.run(metta_script)
        logging.info(f"📊 MeTTa result type: {type(result)}")

        if result and isinstance(result, list) and len(result) > 0:
            actual_result = result[0]

            if hasattr(actual_result, 'get_object'):
                raw_status = actual_result.get_object()
                status = str(raw_status).strip().strip('[]').strip('"\' ')
            else:
                raw_status = str(actual_result)
                status = raw_status.strip().strip('[]').strip('"\' ')

            logging.info(f"📊 Extracted status: '{status}' (raw: {raw_status})")

            if status == "Success":
                logging.info(f"✅ Enhanced MeTTa research successful")
                return "Success"  # Data is in context
            else:
                return f"Enhanced MeTTa research error: {status}"
        else:
            return "Enhanced MeTTa research completed but returned no usable result"

    except Exception as e:
        error_msg = f"Enhanced MeTTa execution error: {str(e)}"
        logging.info(f"❌ {error_msg}")
        import traceback
        logging.info(traceback.format_exc())
        return error_msg

# ===============================
# Step 2: Advanced Research Agent
# ===============================
class IntelligentResearchAgent:
    def __init__(self):
        self.api = AdvancedAPIWrapper()
        self.search_history = []
        logging.info("🧠 Initializing enhanced MeTTa integration...")
        self.metta = setup_metta_integration()
        if self.metta:
            logging.info("✅ Enhanced MeTTa integration initialized successfully")
        else:
            logging.info("⚪ Enhanced MeTTa integration not available")

    def smart_query_expansion(self, question: str) -> list:
        """Generate multiple search variations for better coverage"""
        base_query = question.strip()
        variations = [base_query]

        if len(base_query.split()) <= 3:
            additional_variations = [
                f"{base_query} explanation",
                f"{base_query} guide tutorial",
                f"{base_query} latest research",
                f"what is {base_query}",
                f"{base_query} examples applications"
            ]
            variations.extend(additional_variations)
        else:
            additional_variations = [
                f"{base_query} comprehensive guide",
                f"{base_query} recent developments",
                f"{base_query} expert analysis"
            ]
            variations.extend(additional_variations)

        return variations[:3]

    def comprehensive_research(self, question: str, depth: str = "deep") -> Dict[str, Any]:
        """Perform comprehensive multi-query research"""
        start_time = time.time()

        depth_map = {"quick": 5, "medium": 8, "deep": 12}
        num_results = depth_map.get(depth, 8)

        logging.info(f"🔍 Starting comprehensive research on: '{question}'")
        logging.info(f"📊 Depth: {depth} ({num_results} sources)")

        queries = self.smart_query_expansion(question)
        logging.info(f"🎯 Search variations: {len(queries)}")

        all_results = {}
        all_search_data = []

        for i, query in enumerate(queries, 1):
            logging.info(f"   └─ Query {i}/{len(queries)}: {query}")
            search_results = self.api.enhanced_serper_search(query, num_results//len(queries) + 3)

            for result in search_results:
                url = result['link']
                if url not in all_results:
                    all_results[url] = result

            all_search_data.extend(search_results)
            time.sleep(0.5)

        unique_urls = list(all_results.keys())[:num_results]
        logging.info(f"📚 Found {len(unique_urls)} unique sources")

        logging.info("📖 Extracting content...")
        content_results = self.api.batch_content_extraction(unique_urls)

        extraction_time = time.time() - start_time

        research_data = {
            'query': question,
            'search_queries': queries,
            'total_results': len(unique_urls),
            'extraction_time': extraction_time,
            'results': {}
        }

        for url in unique_urls:
            search_meta = all_results.get(url, {})
            content = content_results.get(url, "Content not available")

            url_data = {
                'title': search_meta.get('title', 'Unknown Title'),
                'snippet': search_meta.get('snippet', ''),
                'content': content,
                'source_type': search_meta.get('source', 'unknown'),
                'date': search_meta.get('date', ''),
                'domain': urlparse(url).netloc
            }

            research_data['results'][url] = url_data

        success_rate = len([r for r in content_results.values() if not r.startswith('Error')]) / len(content_results) * 100
        logging.info(f"✅ Content extraction: {success_rate:.1f}% success rate")

        return research_data

    def generate_comprehensive_answer(self, question: str, research_data: Dict[str, Any], model: str = "openai/gpt-4o-mini", use_multi_part: bool = True) -> Dict[str, Any]:
        """Generate intelligent answer from research data with comprehensive source tracking - uses multi-part for longer content by default"""
        logging.info("🤖 Generating comprehensive analysis with source attribution...")
        if use_multi_part:
            logging.info("📜 Using multi-part generation for extended content...")
            result = self.api.generate_comprehensive_multi_part_analysis(question, research_data, model)
        else:
            result = self.api.intelligent_chat(research_data, question, model)
        return result

    def research_with_analysis(self, question: str, depth: str = "deep", model: str = "openai/gpt-4o-mini", use_metta: bool = False) -> Dict[str, Any]:
        """Complete research pipeline with analysis and optional enhanced MeTTa integration"""
        global METTA_RESEARCH_CONTEXT

        research_data = None
        research_method = 'standard'

        depth_map = {"quick": 5, "medium": 8, "deep": 12}
        num_sources = depth_map.get(depth, 8)

        if use_metta and self.metta:
            logging.info("🧠 Using enhanced MeTTa-based research approach...")
            metta_start_time = time.time()
            metta_status = run_enhanced_metta_research(question, num_sources, self.metta)
            metta_time = time.time() - metta_start_time

            if metta_status == "Success":
                logging.info(f"✅ Enhanced MeTTa research successful")
                # Build research_data from MeTTa context
                clean_query = question.strip()
                context = METTA_RESEARCH_CONTEXT.get(clean_query, {})
                search_results = context.get('search_results', [])

                research_data = {
                    'query': question,
                    'search_queries': [question],
                    'total_results': len(search_results[:num_sources]),
                    'extraction_time': metta_time,
                    'results': {}
                }

                for source in search_results[:num_sources]:
                    url = source['url']
                    content = source.get('extracted_content', 'Extraction failed')

                    url_data = {
                        'title': source['title'],
                        'snippet': source['snippet'],
                        'content': content,
                        'source_type': 'metta_enhanced',
                        'date': '',
                        'domain': urlparse(url).netloc
                    }

                    research_data['results'][url] = url_data

                research_method = 'enhanced_metta'
            else:
                logging.info(f"⚠️ Enhanced MeTTa research encountered an issue: {metta_status}")
                logging.info("🔄 Falling back to standard research...")
                use_metta = False

        if not use_metta or research_data is None:
            # Standard research pipeline
            research_data = self.comprehensive_research(question, depth)
            research_method = 'standard'

        # Generate analysis using the same method for both - use multi-part for deep depth
        use_multi_part = (depth == "deep")
        analysis_result = self.generate_comprehensive_answer(question, research_data, model, use_multi_part)

        # Prepare final output
        result = {
            'question': question,
            'analysis': analysis_result['analysis'] if isinstance(analysis_result, dict) else analysis_result,
            'source_mapping': analysis_result.get('source_mapping', {}) if isinstance(analysis_result, dict) else {},
            'metadata': {
                'sources_found': research_data['total_results'],
                'search_queries': research_data['search_queries'],
                'extraction_time': research_data['extraction_time'],
                'sources': []
            },
            'research_method': research_method
        }

        # Add source information with enhanced metadata and consistent numbering
        source_index = 1
        successful_sources = []
        for url, data in research_data['results'].items():
            extraction_success = not data['content'].startswith('Error')
            source_info = {
                'url': url,
                'title': data['title'],
                'domain': data['domain'],
                'type': data['source_type'],
                'index': source_index,
                'snippet': data['snippet'],
                'extraction_success': extraction_success
            }
            result['metadata']['sources'].append(source_info)
            if extraction_success:
                successful_sources.append(source_info)
            source_index += 1

        result['metadata']['successful_extractions'] = len(successful_sources)

        # Store in history
        history_item = {
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'sources_count': len(result['metadata']['sources']),
            'method': result.get('research_method', 'standard')
        }
        self.search_history.append(history_item)

        return result

# ===============================
# CLI Backend
# ===============================
import argparse
from fpdf import FPDF

def format_result_for_pdf(result: Dict[str, Any]) -> str:
    """Format the research result as plain text for PDF"""
    analysis = result['analysis']
    metadata = result['metadata']
    source_mapping = result.get('source_mapping', {})
    research_method = result.get('research_method', 'standard')

    output = f"RESEARCH QUESTION: {result['question']}\n\n"
    output += f"RESEARCH METHOD: {research_method.replace('_', ' ').title()}\n\n"
    output += "=== ANALYSIS ===\n"
    output += analysis + "\n\n"

    output += "=== METADATA ===\n"
    output += f"Sources Analyzed: {metadata['sources_found']}\n"
    output += f"Search Queries: {len(metadata['search_queries'])}\n"
    output += f"Processing Time: {metadata['extraction_time']:.1f}s\n"
    output += f"Successful Extractions: {metadata.get('successful_extractions', len(metadata.get('sources', [])))}/{metadata['sources_found']}\n"
    output += f"Sources with Citations: {len(source_mapping)}\n"
    success_rate = (metadata.get('successful_extractions', len(metadata.get('sources', [])))/max(metadata['sources_found'], 1)*100)
    output += f"Extraction Success Rate: {success_rate:.1f}%\n\n"

    output += "=== SOURCES ===\n"
    for i, source in enumerate(metadata['sources'], 1):
        source_data = source
        title_truncated = source_data['title'][:60] + "..." if len(source_data['title']) > 60 else source_data['title']
        source_index = source_data.get('index', i)

        was_cited = str(source_index) in [str(k) for k in source_mapping.keys()]
        citation_mark = "✔" if was_cited else "⚪"

        method_indicator = ""
        if source_data['type'] == 'metta_enhanced':
            method_indicator = " [Enhanced MeTTa]"
        elif source_data['type'] == 'metta':
            method_indicator = " [MeTTa]"

        extraction_success = source_data.get('extraction_success', True)
        extraction_mark = "✔" if extraction_success else "⚠️"

        output += f"{citation_mark}{extraction_mark} Source {source_index}. {title_truncated}{method_indicator}\n"
        output += f"   URL: {source_data['url']}\n"
        output += f"   Domain: {source_data['domain']} | Type: {source_data['type'].replace('_', ' ').title()}\n"
        if source_data.get('snippet'):
            snippet_preview = source_data['snippet'][:80] + "..."
            output += f"   Preview: {snippet_preview}\n"
        citation_status = "Referenced in analysis" if was_cited else "Available but not cited"
        extraction_status = "Successful extraction" if extraction_success else "Extraction issues"
        output += f"   Status: {citation_status} | {extraction_status}\n\n"

    # Show MeTTa context info if available
    if METTA_RESEARCH_CONTEXT:
        context = METTA_RESEARCH_CONTEXT.get(result['question'].strip(), {})
        if context:
            output += "=== METTA RESEARCH CONTEXT ===\n"
            output += f"Search Results Found: {len(context.get('search_results', []))}\n"
            output += f"Successful Extractions: {context.get('successful_extractions', 0)}\n"
            output += f"Research Timestamp: {context.get('timestamp', 'Unknown')}\n"

    return output

def main():
    parser = argparse.ArgumentParser(description="Advanced Multi-Source Research Agent CLI Backend")
    parser.add_argument("question", type=str, help="The research question to investigate")
    parser.add_argument("--depth", type=str, default="medium", choices=["quick", "medium", "deep"], help="Research depth (quick: 5 sources, medium: 8, deep: 12)")
    parser.add_argument("--model", type=str, default="openai/gpt-4o-mini", help="AI model for analysis (e.g., openai/gpt-4o-mini, openai/gpt-4o, anthropic/claude-3.5-sonnet, meta-llama/llama-3.1-405b-instruct)")
    parser.add_argument("--use_metta", action="store_true", help="Enable enhanced MeTTa integration for multi-source processing")
    parser.add_argument("--output_dir", type=str, default="raw/", help="Directory to store the output PDF (default: raw/)")

    args = parser.parse_args()

    logging.info("\n🧠 ADVANCED MULTI-SOURCE RESEARCH AGENT CLI")
    logging.info("=" * 60)
    logging.info(f"Research Question: {args.question}")
    logging.info(f"Depth: {args.depth}")
    logging.info(f"Model: {args.model}")
    logging.info(f"Use MeTTa: {'Yes' if args.use_metta else 'No'}")
    logging.info(f"Output Directory: {args.output_dir}")
    logging.info("=" * 60)

    agent = IntelligentResearchAgent()

    try:
        result = agent.research_with_analysis(args.question, args.depth, args.model, args.use_metta)

        # Format content for PDF
        pdf_content = format_result_for_pdf(result)

        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)  # Smaller font for long content
        pdf.multi_cell(0, 5, pdf_content)  # Smaller line height for density

        # Create output dir if not exists
        os.makedirs(args.output_dir, exist_ok=True)

        # Generate filename
        safe_question = re.sub(r'[^\w\s-]', '', args.question[:50]).strip().replace(' ', '_')
        filename = f"research_{safe_question}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = os.path.join(args.output_dir, filename)

        pdf.output(path)

        logging.info(f"✅ Research complete. PDF saved to: {path}")

    except Exception as e:
        logging.info(f"❌ Error during research: {str(e)}")
        import traceback
        logging.info("Full traceback:")
        logging.info(traceback.format_exc())

if __name__ == "__main__":
    main()

logging.info("\n✅ Advanced Research Agent CLI backend initialized successfully!")
logging.info("🔧 Key features:")
logging.info("   • CLI arguments for question, depth, model, use_metta, output_dir")
logging.info("   • Compiles full research result (analysis + metadata + sources) into PDF")
logging.info("   • Stores PDF in specified directory (default: raw/) with timestamped filename")
logging.info("   • Handles long content with smaller font and line height in PDF")
logging.info("   • Requires fpdf library (pip install fpdf)")
logging.info("   • Set API keys via environment variables: SERPER_API_KEY, JINA_API_KEY, OPENROUTER_API_KEY")