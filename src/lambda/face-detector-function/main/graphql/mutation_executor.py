import os
import json
import timeit
from requests_aws4auth import AWS4Auth
from boto3 import Session
from gql import gql
from gql.client import Client
from gql.transport.requests import RequestsHTTPTransport

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='face-detector', child=True)
tracer = Tracer(service='face-detector')

@tracer.capture_method(capture_response=False)
def make_mutation(mutation: dict, variables: dict, gql_endpoint: str) -> str:
    start_time = timeit.default_timer()

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    aws = Session(
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        aws_session_token=os.environ["AWS_SESSION_TOKEN"],
        region_name=os.environ["AWS_REGION"]
    )

    credentials = aws.get_credentials().get_frozen_credentials()

    auth = AWS4Auth(
        os.environ["AWS_ACCESS_KEY_ID"],
        os.environ["AWS_SECRET_ACCESS_KEY"],
        os.environ["AWS_REGION"],
        'appsync',
        session_token=os.environ["AWS_SESSION_TOKEN"],
    )

    transport = RequestsHTTPTransport(
        url=os.environ["GRAPHQL_API_ENDPOINT"],
        headers=headers,
        auth=auth
    )

    client = Client(transport=transport, fetch_schema_from_transport=False)

    try:
        resp = client.execute(gql(mutation), variable_values=(json.dumps({
            "cameraId": variables["cameraId"],
            "ts": variables["ts"],
            "persons": variables["persons"],
            "s3url": variables["s3url"],
            "status": variables["status"]
        })))
    except Exception:
        logger.exception("Error making AppSync mutation")
    
    logger.info(
        f'GraphQL mutation execution completed after: {timeit.default_timer() - start_time}')
