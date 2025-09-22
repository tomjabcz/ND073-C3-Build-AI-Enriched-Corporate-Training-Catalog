import logging
import json
import requests
import azure.functions as func

CROSSREF_API_ENDPOINT = "https://api.crossref.org/works"

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("CrossrefLookup: Python HTTP trigger function processed a request.")

    try:
        data = req.get_json()
    except Exception:
        return func.HttpResponse(
            "The request schema does not match expected schema.",
            status_code=400
        )

    if "Values" not in data or not isinstance(data["Values"], list):
        return func.HttpResponse(
            "The request schema does not match expected schema. Could not find values array.",
            status_code=400
        )

    response = {"Values": []}

    for record in data["Values"]:
        if record is None or "RecordId" not in record:
            continue

        response_record = {
            "RecordId": record["RecordId"],
            "Data": {},
            "Errors": [],
            "Warnings": []
        }

        try:
            article_name = record.get("Data", {}).get("ArticleName")
            if article_name:
                response_record["Data"] = get_entity_metadata(article_name)
        except Exception as e:
            logging.error(f"Error while fetching Crossref metadata: {e}")
            response_record["Errors"].append({"Message": str(e)})
        finally:
            response["Values"].append(response_record)

    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )


def get_entity_metadata(title: str):
    """
    Vyhledá článek přes Crossref REST API a vrátí metadata
    pouze pokud se najde přesná shoda na title (case-insensitive).
    """
    result = {
        "PublicationName": "",
        "Publisher": "",
        "DOI": "",
        "PublicationDate": ""
    }

    params = {
        "query.title": title,
        "rows": 10
    }

    r = requests.get(CROSSREF_API_ENDPOINT, params=params)
    r.raise_for_status()
    data = r.json()

    items = data.get("message", {}).get("items", [])
    for item in items:
        item_title = " ".join(item.get("title", [])).strip()
        if item_title.lower() == title.lower():
            result["DOI"] = item.get("DOI", "")
            result["PublicationDate"] = item.get("published-online", {}).get("date-parts", [[""]])[0]
            result["PublicationName"] = item_title
            result["Publisher"] = item.get("publisher", "")
            break

    return result


def parse_crossref_date(item):
    """
    Vrátí datum ve formátu YYYY-MM-DD pokud je dostupné,
    jinak jen YYYY nebo YYYY-MM.
    """
    published = item.get("published-print") or item.get("published-online")
    if published and "date-parts" in published:
        parts = published["date-parts"]
        return "-".join(str(p) for p in parts)
    return ""
