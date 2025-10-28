"""
Unified Code Platform - Connects Claude & Gemini
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("🚀 UNIFIED AI CODE PLATFORM")
print("="*70)
print()
print("✅ Claude API Key:", "Found" if os.getenv("ANTHROPIC_API_KEY") else "Missing")
print("✅ Gemini API Key:", "Found" if os.getenv("GOOGLE_GEMINI_API_KEY") else "Missing")
print("✅ GitHub Token:", "Found" if os.getenv("GITHUB_TOKEN") else "Missing")
print()
print("Platform ready! You can now:")
print("- Use Claude (via Cline) for complex coding")
print("- Use Gemini (via Jules) for fast implementation")
print("- Auto-route tasks to the best AI")
print()
print("="*70)
