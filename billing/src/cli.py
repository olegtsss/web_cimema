import argparse
import asyncio

from loguru import logger
import uvloop

from services.job import job_service

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


JOBS_MAPPING = {
    "check_new_free_orders": job_service.check_new_free_orders,
    "check_new_orders": job_service.check_new_orders,
    "check_active_recurent_orders": job_service.check_active_recurent_orders,
    "check_expired_orders": job_service.check_expired_orders,
}


async def run():
    parser = argparse.ArgumentParser(description="Run job service tasks.")
    parser.add_argument("job", type=str, choices=JOBS_MAPPING.keys(), help="Job to run")
    args = parser.parse_args()

    coro = JOBS_MAPPING.get(args.job)
    if coro is not None:
        logger.info(f"Job '{args.job}' started")

        try:
            await coro()
        except Exception:
            logger.exception(f"Job '{args.job}' failed")
        else:
            logger.info(f"Job '{args.job}' successfully finished")
    else:
        logger.error(f"Called invalid job '{args.job}'")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
