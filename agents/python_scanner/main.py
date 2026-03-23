"""Entry point for NetScope Python scanner agent."""
import asyncio

from scanner.main import main

if __name__ == "__main__":
    asyncio.run(main())
