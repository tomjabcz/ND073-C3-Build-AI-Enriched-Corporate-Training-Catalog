import logging
import json
import requests
import azure.functions as func

API_KEY = "984786fb75a794f12eb02ae472658534" # Open access api
#API_KEY = "8ff7209a8bd83332257be5c6e57eb74b" # meta api
SPRINGER_API_ENDPOINT = "https://api.springernature.com/openaccess/json"

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("SpringerLookup: Python HTTP trigger function processed a request.")

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
            response_record["Errors"].append({"Message": str(e)})
        finally:
            response["Values"].append(response_record)

    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )


def get_entity_metadata(title: str):
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
    for record in springer_results.get("records", []):
        result["DOI"] = record.get("doi", "")
        result["PublicationDate"] = record.get("publicationDate", "")
        result["PublicationName"] = record.get("publicationName", "")
        result["Publisher"] = record.get("publisher", "")

    return result
