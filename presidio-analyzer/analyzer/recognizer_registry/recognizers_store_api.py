import logging
import os

import grpc
import recognizers_store_pb2
import recognizers_store_pb2_grpc

from analyzer import PatternRecognizer
from analyzer import Pattern


class RecognizerStoreApi:
    """ The RecognizerStoreApi is the object that talks to the remote
    recognizers store service and get the recognizers / timestamp
    """

    def __init__(self):
        try:
            recognizers_store_svc_url = \
                os.environ["RECOGNIZERS_STORE_SVC_ADDRESS"]
        except KeyError:
            recognizers_store_svc_url = "localhost:3004"

        channel = grpc.insecure_channel(recognizers_store_svc_url)
        self.rs_stub = recognizers_store_pb2_grpc.RecognizersStoreServiceStub(
            channel)

    def get_latest_timestamp(self):
        """
        Returns the timestamp (unix style) of when the store was last updated.
        0 if not found
        """
        timestamp_request = \
            recognizers_store_pb2.RecognizerGetTimestampRequest()
        lst_update = 0
        try:
            lst_update = self.rs_stub.ApplyGetTimestamp(
                timestamp_request).unixTimestamp
        except grpc.RpcError:
            logging.info("Failed to get timestamp")
            return 0

        logging.info("Latest timestamp found in store is: %d", lst_update)
        return lst_update

    def get_all_recognizers(self):
        """
        Returns a list of CustomRecognizer which were created from the
        recognizers stored in the underlying store
        """
        req = recognizers_store_pb2.RecognizersGetAllRequest()
        raw_recognizers = []

        try:
            raw_recognizers = self.rs_stub.ApplyGetAll(req).recognizers

        except grpc.RpcError:
            logging.info("Failed getting recognizers from the remote store. \
            Returning an empty list")
            return raw_recognizers

        custom_recognizers = []
        for new_recognizer in raw_recognizers:
            patterns = []
            for pat in new_recognizer.patterns:
                patterns.extend(
                    [Pattern(pat.name, pat.regex, pat.score)])
            new_custom_recognizer = PatternRecognizer(
                name=new_recognizer.name,
                supported_entity=new_recognizer.entity,
                supported_language=new_recognizer.language,
                black_list=new_recognizer.blacklist,
                context=new_recognizer.contextPhrases,
                patterns=patterns)
            custom_recognizers.append(
                new_custom_recognizer)

        return custom_recognizers
