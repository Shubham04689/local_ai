#!/usr/bin/env python3
"""
Universal AI Chatbot - Main entry point
Runs startup launcher which checks providers, starts server.
"""
import sys
import asyncio
from startup.launcher import main

if __name__ == "__main__":
    try:
        print("🚀 Starting Universal AI Chatbot...")
        print("🔧 Multi-provider support enabled")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        sys.exit(1)
