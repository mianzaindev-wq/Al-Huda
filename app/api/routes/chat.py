"""
api/routes/chat.py
------------------
/chat  — standard (non-streaming) chat endpoint
/chat-stream — Server-Sent Events streaming endpoint

Both endpoints share the same context-building logic:
  1. Detect and scrape any URLs in the message
  2. Run vector search against the Islamic knowledge base
  3. Call Mistral with a full system prompt + chat history
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.models import ChatRequest, ChatResponse
from app.core.config import GENERATION_CONFIG, MAX_CHAT_MESSAGES, MISTRAL_MODEL
from app.services.chat_memory import chat_memory
from app.services.mistral_client import call_mistral_api, mistral_client, verify_islamic_citations
from app.services.vector_db import vector_db
from app.services.web_scraper import detect_urls_in_message, extract_web_content_via_mistral

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a warm, knowledgeable Islamic AI Assistant with deep expertise in \
Hadith, Quranic teachings, and Islamic scholarship.

YOUR PERSONALITY & COMMUNICATION STYLE:
- Be warm, welcoming, and genuinely caring — treat every questioner as a fellow seeker of knowledge
- Use a conversational yet respectful tone — like a wise friend who happens to be a scholar
- Show enthusiasm for helping others understand Islam's beautiful teachings
- Express concepts in accessible, relatable language while maintaining scholarly accuracy
- Share the wisdom and beauty behind Islamic teachings, not just the rules
- Use "we" and "us" to create a sense of shared journey in seeking knowledge

YOUR RESPONSE STRUCTURE:
For most responses, follow this optimal structure:
1. **Warm Opening** (1-2 sentences): Brief, welcoming acknowledgment
2. **Main Content** (2-4 structured sections): Core explanation with clear headings
3. **Quranic Context** (when relevant): Include relevant verses with references
4. **Practical Wisdom** (if applicable): Real-world application and benefits
5. **Closure** (1-2 sentences): Inspiring conclusion with Islamic greeting

FORMATTING FOR MAXIMUM READABILITY & STRUCTURE:
- Use ## headings to structurally divide your response into clear sections
- Use ### for subsections within major topics
- Keep paragraphs to 3-4 sentences maximum for better readability
- Use bullet lists (*) for related points that aren't sequential
- Use numbered lists (1. 2. 3.) ONLY for sequential steps
- Add visual spacing between major concepts using blank lines
- Break complex ideas into digestible chunks

RESPONSE LENGTH GUIDELINES:
- Simple questions: 30-80 words, 1 short section
- Standard questions: 100-200 words, 2 sections with 1 citation max
- Complex topics: up to 300 words maximum, 2-3 sections
- HARD RULE: You MUST complete your entire response within these limits. NEVER exceed 300 words of your own text.
- CRITICAL: Quran/Hadith citations consume ~30% of your space. Budget accordingly — if you include a citation, keep your surrounding text shorter.
- If a topic requires more depth, provide a focused summary and offer to elaborate on specific aspects.
- Prioritize completeness over comprehensiveness — a finished short answer is always better than a cut-off long one.
- ALWAYS end with a complete concluding sentence. If you sense you are running out of space, immediately wrap up with a brief closing.
- NEVER end mid-sentence, mid-list, or mid-paragraph. Plan your response to finish cleanly.
- NEVER start or finish abruptly

REQUIRED QURAN & HADITH SYNTAX:

For Quran verses (MANDATORY - include both Arabic and English):
  [Quran:Surah Name Chapter:Verse|Arabic Text|English Translation]
  Example: [Quran:Al-Baqarah 2:286|لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا|Allah does not burden a soul beyond that it can bear]

For Hadith (MANDATORY - include collection, number, and full text):
  [Hadith:Collection Name and Number|"Exact hadith text in English"|Optional Narrator]
  Example: [Hadith:Sahih Bukhari 6502|"The best among you are those who have the best manners and character."|Narrated by Abdullah ibn Amr]

MARKDOWN FORMATTING:

HEADINGS (proper hierarchy):
## Main Section Title
### Subsection Title
#### Minor Points

LISTS (context required):
- Always introduce lists with context: "There are three key aspects:"
- For sequential items: use numbered lists
- For related items: use bullet points
- Always close lists with a connecting sentence

TABLES (always introduce):
Format: | Header 1 | Header 2 |
        |----------|----------|
        | Data     | Data     |

BLOCKQUOTES:
> Use for important standalone teachings or prophecies

EMPHASIS:
- **bold** for key Islamic terms and critical concepts
- *italic* for foreign Arabic terms, names, or titles

CRITICAL CONTENT RULES:
1. SOURCE INTEGRITY — Use ONLY authenticated Islamic sources
2. ACCURACY — Precision over speculation; refer to scholars if uncertain
3. COMPLETENESS — Always finish every response with a complete thought
4. CITATIONS — Always include source references for major claims
5. AUTHENTICITY — Include Hadith collection names and numbers
6. READABILITY — Prioritize clarity and structure over word count

ENHANCED RESPONSE QUALITY:

For Explanations:
- Start with the essence, then expand
- Use analogies to make complex concepts relatable
- Include both theoretical and practical understanding

For Comparisons:
- Use tables or structured lists
- Highlight key differences clearly
- Provide Islamic reasoning for each point

For Step-by-Step Guidance:
- Number steps sequentially
- Include practical aids or reminders
- Explain the Islamic basis for each step

For Wisdom/Teachings:
- Quote relevant Quranic verses or Hadith
- Explain the deeper meaning and benefits
- Apply to contemporary life where appropriate

CONTENT QUALITY STANDARDS:
- Provide 2-3 Quranic or Hadith references for most responses
- For each major claim, include at least one source
- Include practical examples and real-life applications
- Connect abstract concepts to daily Islamic living
- Maintain scholarly accuracy with accessible language

CLOSING GUIDANCE:
- End with an inspiring statement or Islamic greeting
- Leave the reader with a clear takeaway
- Encourage continued learning and reflection
- May your responses be a means of genuine benefit and guidance. Āmīn."""


# ---------------------------------------------------------------------------
# Shared context builder
# ---------------------------------------------------------------------------

async def _build_context(req: ChatRequest, conversation_id: str):
    """Fetch vector search results and optional web content for a message."""
    user_message = req.message

    # 1. Web content from any URLs in the message
    detected_urls = detect_urls_in_message(user_message)
    web_content = ""
    web_extraction_performed = False
    if detected_urls:
        logger.info(f"Detected {len(detected_urls)} URL(s) in message")
        web_content = await extract_web_content_via_mistral(detected_urls, user_message)
        if web_content:
            web_extraction_performed = True

    # 2. Semantic vector search
    relevant_context = ""
    sources_used: List[Dict] = []
    context_chunks = 0

    if req.use_vector_search and vector_db.texts:
        search_results = await vector_db.search_async(user_message, k=5, min_score=0.3)
        if search_results:
            context_chunks = len(search_results)
            context_parts = ["\n\nRELEVANT CONTEXT FROM DATABASE:"]
            for i, result in enumerate(search_results, 1):
                relevance = result["similarity_score"]
                context_parts.append(
                    f"\n[Context {i}] (Relevance: {relevance:.1%})\n"
                    f"Source: {result['metadata'].get('source', 'unknown')}\n"
                    f"{result['text']}\n"
                    f"{'-' * 50}"
                )
                sources_used.append({
                    "source": result["metadata"].get("source", "unknown"),
                    "type": result["metadata"].get("type", "unknown"),
                    "relevance": float(relevance),
                })
            relevant_context = "\n".join(context_parts)
            logger.info(f"Vector search: {len(search_results)} contexts retrieved")

    # 3. Compose user content block
    # Build context hierarchy: database → web content → user question
    content_parts = [
        relevant_context if relevant_context else "No specific Islamic knowledge base context available."
    ]
    
    if web_content:
        content_parts.append(f"\nWEB CONTENT EXTRACTED:\n{web_content}")
    
    content_parts.extend([
        f"\nUSER QUESTION:\n{user_message}",
        "\nPlease provide a helpful, accurate response with proper citations:"
    ])
    
    user_content = "".join(content_parts)

    return user_content, sources_used, context_chunks, web_extraction_performed


# ---------------------------------------------------------------------------
# /chat — standard endpoint
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Full chat response (non-streaming). Includes vector search + chat history."""
    start_time = time.time()
    conversation_id = req.conversation_id or f"chat_{int(time.time() * 1000)}"

    logger.info(f"[chat] conversation={conversation_id} | message='{req.message[:80]}…'")

    try:
        chat_memory.add_message(conversation_id, "user", req.message)

        user_content, sources_used, context_chunks, web_extraction_performed = (
            await _build_context(req, conversation_id)
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *chat_memory.get_formatted_history(conversation_id, limit=5),
            {"role": "user", "content": user_content},
        ]

        full_response = await call_mistral_api(messages)
        full_response = verify_islamic_citations(full_response)

        chat_memory.add_message(
            conversation_id,
            "assistant",
            full_response,
            metadata={"sources_used": len(sources_used), "web_extraction": web_extraction_performed},
        )

        messages_in_chat = len(chat_memory.get_history(conversation_id))
        processing_time = round(time.time() - start_time, 2)
        logger.info(f"[chat] Response ready in {processing_time}s ({len(full_response)} chars)")

        return ChatResponse(
            reply=full_response,
            timestamp=datetime.now().isoformat(),
            conversation_id=conversation_id,
            status="success",
            sources_used=sources_used or None,
            context_chunks=context_chunks or None,
            web_extraction_performed=web_extraction_performed,
            messages_in_chat=messages_in_chat,
            processing_time=processing_time,
        )

    except Exception as exc:
        logger.error(f"[chat] Error: {exc}", exc_info=True)
        err = str(exc).lower()
        if "401" in err or "unauthorized" in err or "invalid api key" in err:
            user_msg = "⚠️ AI service authentication failed. The API key may be invalid or expired."
        elif "403" in err or "forbidden" in err:
            user_msg = "🚫 Access denied by the AI service. Your API key may not have permission for this model."
        elif "quota" in err or "429" in err or "rate limit" in err or "too many" in err:
            user_msg = "⏳ The AI service is experiencing high demand. Please wait a moment and try again. 🙏"
        elif "timeout" in err or "timed out" in err:
            user_msg = "⏱️ The request took too long. Please try with a shorter message."
        elif any(kw in err for kw in ("connect", "getaddrinfo", "network", "unreachable", "dns", "ssl")):
            user_msg = "🌐 Unable to connect to the AI service. Please check your internet connection and try again."
        elif "model" in err and ("not found" in err or "does not exist" in err):
            user_msg = "🔧 The configured AI model is unavailable. Please contact the administrator."
        elif "empty response" in err:
            user_msg = "The AI returned an empty response. Please try rephrasing your question."
        elif "content" in err and ("filter" in err or "blocked" in err or "safety" in err):
            user_msg = "🛡️ Your message was blocked by content safety filters. Please rephrase your question."
        else:
            user_msg = f"An error occurred ({type(exc).__name__}). Please try again."
        return ChatResponse(
            reply=user_msg,
            timestamp=datetime.now().isoformat(),
            conversation_id=conversation_id,
            status="error",
            processing_time=round(time.time() - start_time, 2),
        )


# ---------------------------------------------------------------------------
# /chat-stream — Server-Sent Events endpoint
# ---------------------------------------------------------------------------

@router.post("/chat-stream")
async def chat_stream_endpoint(req: ChatRequest):
    """Streaming chat using Server-Sent Events. Falls back to simulated streaming
    if the Mistral SDK version does not expose stream_async."""
    conversation_id = req.conversation_id or f"chat_{int(time.time() * 1000)}"

    async def generate_stream():
        try:
            chat_memory.add_message(conversation_id, "user", req.message)

            user_content, sources_used, _, _ = await _build_context(req, conversation_id)

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *chat_memory.get_formatted_history(conversation_id, limit=5),
                {"role": "user", "content": user_content},
            ]

            full_response = ""

            # Try native streaming; fall back to simulated chunking
            if hasattr(mistral_client.chat, "stream_async"):
                async for chunk in await mistral_client.chat.stream_async(
                    model=MISTRAL_MODEL, messages=messages, **GENERATION_CONFIG
                ):
                    if chunk.data.choices:
                        delta = chunk.data.choices[0].delta.content
                        if delta:
                            full_response += delta
                            yield f"data: {json.dumps({'type': 'chunk', 'content': delta})}\n\n"
                            await asyncio.sleep(0.01)
            else:
                # Fallback: get full response then stream it in appropriate chunks
                # Scale chunk size and delay based on response length for natural flow
                response = await mistral_client.chat.complete_async(
                    model=MISTRAL_MODEL, messages=messages, **GENERATION_CONFIG
                )
                if response and response.choices:
                    full_response = response.choices[0].message.content
                    # Adaptive chunking: larger responses get bigger chunks
                    chunk_size = max(15, min(50, len(full_response) // 20))
                    chunk_delay = 0.02 if len(full_response) > 500 else 0.04
                    
                    for i in range(0, len(full_response), chunk_size):
                        piece = full_response[i : i + chunk_size]
                        yield f"data: {json.dumps({'type': 'chunk', 'content': piece})}\n\n"
                        await asyncio.sleep(chunk_delay)

            chat_memory.add_message(conversation_id, "assistant", full_response)
            yield f"data: {json.dumps({'type': 'complete', 'sources': sources_used})}\n\n"

        except Exception as exc:
            logger.error(f"[chat-stream] Error: {exc}", exc_info=True)
            err = str(exc).lower()

            # Classify the error for a precise user-facing message
            if "401" in err or "unauthorized" in err or "invalid api key" in err:
                error_msg = "⚠️ AI service authentication failed. The API key may be invalid or expired. Please contact the administrator."
            elif "403" in err or "forbidden" in err:
                error_msg = "🚫 Access denied by the AI service. Your API key may not have permission for this model."
            elif "429" in err or "quota" in err or "rate limit" in err or "too many" in err:
                error_msg = "⏳ The AI service is experiencing high demand. Please wait a moment and try again."
            elif "timeout" in err or "timed out" in err:
                error_msg = "⏱️ The request took too long to process. Try asking a shorter or simpler question."
            elif any(kw in err for kw in ("getaddrinfo", "connect", "connection refused",
                                           "network", "unreachable", "name resolution",
                                           "dns", "ssl", "certificate")):
                error_msg = "🌐 Unable to reach the AI service. Please check your internet connection and try again."
            elif "model" in err and ("not found" in err or "does not exist" in err):
                error_msg = "🔧 The configured AI model is unavailable. Please contact the administrator."
            elif "empty response" in err:
                error_msg = "The AI returned an empty response. Please try rephrasing your question."
            elif "content" in err and ("filter" in err or "blocked" in err or "safety" in err):
                error_msg = "🛡️ Your message could not be processed due to content safety filters. Please rephrase your question."
            elif "validation" in err or "invalid" in err:
                error_msg = "❌ There was an issue with the request format. Please try again with a different message."
            else:
                error_msg = f"An unexpected error occurred: {type(exc).__name__}. Please try again."

            err_payload = {"type": "error", "message": error_msg}
            yield f"data: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
