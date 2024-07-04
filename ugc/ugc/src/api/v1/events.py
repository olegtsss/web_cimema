from flask import Blueprint, g

from api.v1.utils import (
    exception_handler, proccess_event, validate_request_headers
)
from buses.bus import get_eventbus
from schemas.entity import (
    ClickEvent,
    VisitEvent,
)

eventbus = get_eventbus()

router = Blueprint("events", __name__)


@router.route("/click", methods=["POST"])
@exception_handler
@validate_request_headers
def create_click_event():
    """Ручка создания события типа "клик"."""
    event_model = ClickEvent
    event_data = g.request_data
    return proccess_event(event_model, event_data)


@router.route("/visit", methods=["POST"])
@exception_handler
@validate_request_headers
def create_visit_event():
    """Ручка создания события типа "визит"."""
    event_model = VisitEvent
    event_data = g.request_data
    return proccess_event(event_model, event_data)


@router.route("/exception", methods=["POST"])
@exception_handler
@validate_request_headers
def raise_exception():
    """Искусственное возбуждение исключения внутри роута."""
    raise Exception("Some error")
