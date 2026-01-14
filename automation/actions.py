import json
import os
import re
import shutil
import subprocess
import time
import webbrowser
import pyautogui
import requests
from bs4 import BeautifulSoup

from config import trace_logger
from ollama.client import ollama_generate
from ollama.prompts import ACTION_PARSER_PROMPT


ACTION_MODEL = "qwen3:4b"


def _extract_json(text: str):
    match = re.search(r"\{[\s\S]*?\}", text)
    return match.group() if match else None


def parse_action_command(text: str) -> dict:
    trace_logger.info("Action parsing started")
    start = time.perf_counter()

    raw_response = ollama_generate(
        model=ACTION_MODEL,
        prompt=ACTION_PARSER_PROMPT.replace("{user_input}", text),
    )

    duration = time.perf_counter() - start
    trace_logger.info(
        f"Action parser responded | duration={duration:.3f}s"
    )

    json_str = _extract_json(raw_response)
    if not json_str:
        return {"action": "none"}

    try:
        parsed = json.loads(json_str)
        trace_logger.info(
            f"Action parsed successfully: {parsed.get('action')}"
        )
        return parsed
    except Exception as e:
        trace_logger.error(f"Failed to parse action JSON: {e}")
        return {"action": "none"}


# ======================================================
# ENTRY POINT
# ======================================================

def execute_action(action_data):
    if not action_data or action_data.get("action") == "none":
        return "I didn't find anything to do."

    action = action_data.get("action")

    if action == "open_app":
        return open_app(action_data.get("target"))

    if action == "search_web":
        return search_web(
            action_data.get("query"),
            action_data.get("engine")
        )

    if action == "system_control":
        return system_control(
            action_data.get("command"),
            action_data.get("value")
        )

    return "That action isn't supported."


# ======================================================
# OPEN ANY APP (DYNAMIC)
# ======================================================

def open_app(target):
    if not target:
        return "Which app should I open?"

    target = target.strip()
    trace_logger.info(f"Attempting to open app: {target}")

    try:
        # Press Windows key
        pyautogui.press('win')
        time.sleep(1)
        
        # Type the app name
        pyautogui.write(target)
        time.sleep(1)
        
        # Press Enter
        pyautogui.press('enter')
        
        trace_logger.info(f"Successfully opened app: {target}")
        return f"Opening {target}."
    
    except Exception as e:
        trace_logger.error(f"Failed to open app: {e}")
        return f"I couldn't open {target}."


# ======================================================
# SEARCH ANYTHING (DYNAMIC)
# ======================================================

def search_web(query, engine=None):
    if not query:
        return "What should I search for?"

    engine = (engine or "google").lower()
    trace_logger.info(f"Web search started | engine={engine} | query={query}")

    try:
        # Use DuckDuckGo for scraping (no CAPTCHA)
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        
        # Make request with headers to mimic browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract top 10 URLs from DuckDuckGo results
        urls = []
        results = soup.find_all('a', class_='result__a', limit=10)
        
        for result in results:
            href = result.get('href')
            if href:
                # DuckDuckGo uses redirect URLs, extract actual URL
                if 'uddg=' in href:
                    # Extract from uddg parameter
                    match = re.search(r'uddg=([^&]+)', href)
                    if match:
                        import urllib.parse
                        actual_url = urllib.parse.unquote(match.group(1))
                        urls.append(actual_url)
                else:
                    urls.append(href)
        
        trace_logger.info(f"Scraped {len(urls)} URLs from search results")
        
        # Get the first URL
        if urls:
            first_url = urls[0]
            trace_logger.info(f"Opening first URL: {first_url}")
            
            # Open in default browser
            webbrowser.open(first_url)
            
            return f"Opening the top result for {query}."
        else:
            trace_logger.warning("No URLs found in search results")
            return f"Couldn't find results for {query}."
    
    except Exception as e:
        trace_logger.error(f"Web search error: {e}")
        return f"I couldn't complete the search for {query}."
        # Fallback: just open the search page
        fallback_url = f"https://www.google.com/search?q={query}"
        webbrowser.open(fallback_url)
        return f"Searching for {query}."


# ======================================================
# SYSTEM CONTROL (DYNAMIC, SAFE)
# ======================================================

def system_control(command, value=None):
    if not command:
        return "System command missing."

    cmd = command.lower()
    trace_logger.info(f"System control: {cmd} {value}")

    # 🔒 SAFE COMMANDS ONLY
    if cmd in ["lock", "lock screen"]:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Locking the screen."

    if cmd in ["shutdown"]:
        os.system("shutdown /s /t 5")
        return "Shutting down the system."

    if cmd in ["restart"]:
        os.system("shutdown /r /t 5")
        return "Restarting the system."

    if cmd in ["volume"]:
        if value == "up":
            os.system("nircmd.exe changesysvolume 5000")
            return "Turning volume up."
        if value == "down":
            os.system("nircmd.exe changesysvolume -5000")
            return "Turning volume down."

    return "That system command is not allowed."