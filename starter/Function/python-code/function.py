import logging
import json
import requests
import azure.functions as func

# Springer API konfigurace
API_KEY = "984786fb75a794f12eb02ae472658534"
SPRINGER_API_ENDPOINT = "http://api.springernature.com/openaccess/json"


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Entity Search function: Python HTTP trigger function processed a request.")

    try:
        request_body = req.get_body()
        data = json.loads(request_body)
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
    Zavolá Springer API a vrátí metadata článku (DOI, PublicationDate, PublicationName, Publisher)
    """
    result = {
        "PublicationName": "",
        "Publisher": "",
        "DOI": "",
        "PublicationDate": ""
    }

    uri = f"{SPRINGER_API_ENDPOINT}?q=title:\"{title}\"&api_key={API_KEY}"
    r = requests.get(uri)
    r.raise_for_status()

    springer_results = r.json()
    records = springer_results.get("records", [])

    for record in records:
        result["DOI"] = record.get("doi", "")
        result["PublicationDate"] = record.get("publicationDate", "")
        result["PublicationName"] = record.get("publicationName", "")
        result["Publisher"] = record.get("publisher", "")

    return result
