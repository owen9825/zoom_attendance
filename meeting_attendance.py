import os
from typing import List, Optional

import requests

from helpers import get_colored_logger
from pyzoom import ZoomClient
from pyzoom.schemas import MeetingParticipant, ZoomMeetingShort

logger = get_colored_logger()

auth_token_url = "https://zoom.us/oauth/token"
api_base_url = "https://api.zoom.us/v2"


def get_access_token(account_id: str) -> Optional[str]:
    # https://developers.zoom.us/docs/internal-apps/s2s-oauth/
    client_id = os.getenv("ZOOM_CLIENT_ID")
    client_secret = os.getenv("ZOOM_CLIENT_SECRET")
    # https://www.makeuseof.com/generate-server-to-server-oauth-zoom-meeting-link-python/
    data = {
        "grant_type": "account_credentials",
        "account_id": account_id,
        "client_secret": client_secret,
    }
    headers = {"Host": "zoom.us"}
    response = requests.post(
        auth_token_url, auth=(client_id, client_secret), data=data, headers=headers
    )
    if not response.ok:
        logger.warning(
            "There was an error (%s) authenticating at %s: %s",
            response.status_code,
            response.url,
            response.text,
        )
        return None
    body = response.json()
    return body.get("access_token")


def log_attendance_at_meeting(
    api_client: ZoomClient, meeting: ZoomMeetingShort
) -> None:
    logger.debug("Getting participants of meeting %s", meeting.topic)
    participationResponse: List[
        MeetingParticipant
    ] = api_client.meetings.past_meeting_participants(meeting_id=meeting.id)
    # todo: get the next page of participation
    for participant in participationResponse.participants:
        logger.info(
            "%s (%s) attended %s",
            participant.name,
            participant.user_email,
            meeting.topic,
        )


def log_attendance_at_meetings(account_id: str) -> None:
    access_token = get_access_token(account_id)
    if not access_token:
        return None
    api_client = ZoomClient(access_token)
    meetingListResponse = api_client.meetings.list_meetings()
    for meeting in meetingListResponse.meetings:
        # Notice we're only iterating over the first page of meetings
        log_attendance_at_meeting(api_client, meeting)


if __name__ == "__main__":
    account_id = os.getenv("ZOOM_ACCOUNT_ID")
    log_attendance_at_meetings(account_id)
