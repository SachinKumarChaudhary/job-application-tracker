#!/usr/bin/env python3
import time
import signal
import sys

from src.config import POLL_INTERVAL_MINUTES, logger
from src.main import OfferTracker


running = True


def handle_shutdown(signum, frame):
    global running
    logger.info("Shutdown signal received, exiting...")
    running = False


def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    tracker = OfferTracker()
    logger.info(f"Starting scheduler — polling every {POLL_INTERVAL_MINUTES} minutes")

    tracker.run_once()

    while running:
        try:
            time.sleep(POLL_INTERVAL_MINUTES * 60)
            if running:
                tracker.run_once()
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            time.sleep(60)

    logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
