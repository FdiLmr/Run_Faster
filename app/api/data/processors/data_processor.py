"""
Data processing and transformation from stored files into analytics tables.
"""

import time
import logging
from sql_methods import read_db, write_db_replace
from analytics.transformer import transform_athlete_data

logger = logging.getLogger(__name__)


def process_stored_data() -> str:
    """
    Process stored data files into analytics tables.

    Returns:
        str: Summary of the processing operation
    """
    start_time = time.time()
    athletes_processed = 0

    logger.debug("Reading processing_status table from database.")
    processing_status = read_db("processing_status")
    athletes_to_process = len(processing_status[processing_status["status"] == "none"])
    logger.info(f"Found {athletes_to_process} athletes to process (status == 'none').")

    for index, row in processing_status.iterrows():
        athlete_id = int(row["athlete_id"])
        logger.debug(
            f"Processing athlete with ID: {athlete_id}, current status: {row['status']}"
        )

        if athlete_id != 0 and row["status"] in ["none", "processing"]:
            try:
                logger.info(f"Starting transformation for athlete {athlete_id}.")
                transform_athlete_data(athlete_id, populate_all_from_files=1)
                athletes_processed += 1
                logger.info(f"Transformation successful for athlete {athlete_id}.")

                # Only mark as processed if transform was successful
                processing_status.at[index, "status"] = "none"
                write_db_replace(processing_status, "processing_status")
                logger.debug(
                    f"Updated processing_status for athlete {athlete_id} to 'none'."
                )

            except Exception as e:
                logger.error(
                    f"Error processing athlete {athlete_id}: {e}", exc_info=True
                )
                continue

    total_time = time.time() - start_time
    summary = f"""
    Processing Complete:
    ===================
    Athletes processed: {athletes_processed}
    Total processing time: {total_time:.2f} seconds
    """

    logger.info("process_stored_data() completed. " + summary)
    return summary
