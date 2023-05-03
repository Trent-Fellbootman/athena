from dataclasses import dataclass
from ...core import AAISMessagePacket
from typing import Any, Optional


@dataclass
class AAISAPIServerReportPacket(AAISMessagePacket):

    @dataclass
    class ReportMetadata:
        # this field is used to identify an API call record
        # in the API call record table of the parent API server (if any)
        # typically, when a parent diverges an API call to a child,
        # the parent generates an ID for that API call, and the ID
        # is passed to the child.
        # then, when the child returns the result of the API call,
        # it uses that ID to help the parent associate the return
        # message with the correct API call record.
        # if the parent does not have an API call record table
        # (which is the case for non-API server parents, e.g., API callers),
        # this field is None (as the parent will not pass in the ID information
        # when calling the API anyway).
        upstreamApiCallRecordIdentifier: Optional[Any]  # TODO

    reportMetadata: ReportMetadata


@dataclass
class AAISAPIServerAPIRequestRoutePacket(AAISMessagePacket):

    @dataclass
    class RouteMetadata:
        # this field is used to pass in the ID of the API call record
        # in the sender of this packet.
        # then, when the child server reports status to the parent server,
        # it can use this information to help the parent associate the
        # return message with the correct API call record.
        upstreamApiCallRecordIdentifier: Any

    routeMetadata: RouteMetadata
