import argparse
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from requests import Session
from tqdm import tqdm

from src.paths import RAW_LISTINGS_DIR


SEARCH_URL = "https://web.gw.fotocasa.es/v2/propertysearch/search"
DETAIL_URL = "https://web.gw.fotocasa.es/v2/propertysearch/property"

HEADERS = {
    "accept": "application/json,text/plain,*/*",
    "accept-language": "es-ES,es;q=0.9,en;q=0.8",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    ),
}


def search_params(page: int) -> Dict[str, Any]:
    return {
        "combinedLocationIds": "724,9,8,232,376,8019,0,0,0",
        "culture": "es-ES",
        "includePurchaseTypeFacets": "true",
        "isMap": "false",
        "isNewConstructionPromotions": "false",
        "latitude": 41.3854,
        "longitude": 2.17754,
        "pageNumber": page,
        "platformId": 1,
        "propertyTypeId": 2,
        "sortOrderDesc": "true",
        "sortType": "scoring",
        "transactionTypeId": 1,
    }


def request_json(session: Session, url: str, params: Dict[str, Any], timeout: int) -> Optional[Dict[str, Any]]:
    try:
        response = session.get(url, params=params, headers=HEADERS, timeout=timeout)
        if response.status_code == 403:
            logging.warning("Request blocked with status code 403: %s", response.url)
            return None
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        logging.warning("Request failed: %s", error)
    except ValueError as error:
        logging.warning("Could not parse JSON response: %s", error)
    return None


def get_listing_ids(session: Session, page: int, timeout: int) -> List[int]:
    data = request_json(session, SEARCH_URL, search_params(page), timeout)
    if not data:
        return []
    return [item["id"] for item in data.get("realEstates", []) if isinstance(item, dict) and "id" in item]


def flatten_listing(data: Dict[str, Any]) -> Dict[str, Any]:
    address = data.get("address") or {}
    energy = data.get("propertyEnergyCertificate") or {}
    transactions = data.get("transactions") or []
    first_transaction = transactions[0] if transactions else {}
    transaction_values = first_transaction.get("value") or []

    record = {
        "id": data.get("id"),
        "type": data.get("typeId"),
        "subtype": data.get("subtypeId"),
        "external_contract": data.get("isExternalContact"),
        "invalid": data.get("isInvalid"),
        "new": data.get("isNew"),
        "advertiser": (data.get("advertiser") or {}).get("name"),
        "description": (data.get("descriptions") or {}).get("es-ES"),
        "transactions": len(transactions),
        "transaction_type": first_transaction.get("transactionTypeId"),
        "value": transaction_values[0] if transaction_values else None,
        "reduced": first_transaction.get("reduced"),
        "periodicity_id": first_transaction.get("periodicityId"),
        "ubication": address.get("ubication"),
        "zipcode": address.get("zipCode"),
        "highlight": data.get("highlight"),
        "date": data.get("date"),
        "energy_letter": energy.get("energyEfficiencyRatingTypeId"),
        "energy_value": energy.get("energyEfficiencyValue"),
        "environment_letter": energy.get("environmentImpactRatingTypeId"),
        "environment_value": energy.get("environmentImpactValue"),
    }

    multimedia_counts = {}
    for item in data.get("multimedias") or []:
        type_id = item.get("typeId")
        if type_id is not None:
            key = f"multimedia_type_{type_id}"
            multimedia_counts[key] = multimedia_counts.get(key, 0) + 1

    features = {}
    for item in data.get("features") or []:
        if isinstance(item, dict):
            features.update(item)

    feature_list = {}
    for item in data.get("featuresList") or []:
        label = item.get("label")
        if label is not None:
            feature_list[label] = item.get("value")

    other_features = {}
    for item in data.get("otherFeatures") or []:
        if isinstance(item, dict):
            other_features.update({value: key for key, value in item.items()})

    record.update(multimedia_counts)
    record.update(features)
    record.update(feature_list)
    record.update(other_features)
    record.update(address.get("location") or {})
    record.update(address.get("coordinates") or {})

    return record


def collect_listings(start_page: int, end_page: int, delay_seconds: float, timeout: int) -> pd.DataFrame:
    records = []

    with requests.Session() as session:
        for page in tqdm(range(start_page, end_page + 1), desc="Collecting pages"):
            listing_ids = get_listing_ids(session, page, timeout)
            logging.info("Page %s: %s listing IDs collected.", page, len(listing_ids))

            for listing_id in listing_ids:
                params = {"culture": "es-ES", "locale": "es-ES", "transactionType": 1, "periodicityId": 0, "id": listing_id}
                data = request_json(session, DETAIL_URL, params, timeout)

                if data:
                    try:
                        records.append(flatten_listing(data))
                    except Exception as error:
                        logging.warning("Could not parse listing %s: %s", listing_id, error)

                time.sleep(delay_seconds)

    df = pd.DataFrame(records)
    if "id" in df.columns:
        df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect raw Barcelona housing listing data.")
    parser.add_argument("--start-page", type=int, required=True, help="First search-results page to collect.")
    parser.add_argument("--end-page", type=int, required=True, help="Last search-results page to collect.")
    parser.add_argument("--delay-seconds", type=float, default=2.0, help="Delay between listing-detail requests.")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds.")
    parser.add_argument("--output-dir", type=Path, default=RAW_LISTINGS_DIR, help="Directory where raw listing CSV files are saved.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = parse_args()

    if args.end_page < args.start_page:
        raise ValueError("end-page must be greater than or equal to start-page.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    df = collect_listings(args.start_page, args.end_page, args.delay_seconds, args.timeout)

    output_path = args.output_dir / f"listings_{args.start_page}_{args.end_page}.csv"
    df.to_csv(output_path, index=False)
    logging.info("Saved %s listings to %s.", len(df), output_path)


if __name__ == "__main__":
    main()