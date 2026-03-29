"""LLM tool definitions and dispatch — bridges OpenAI function calling to actual services."""

import logging
from typing import Dict, Any, List

from services import calendar, payments, distance

logger = logging.getLogger("service_bot")

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_calendar_events",
            "description": "List upcoming calendar events in a time range. Use when the user asks about existing appointments or schedule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "Start of range in ISO 8601 format (e.g. 2026-04-01T00:00:00Z)"},
                    "end": {"type": "string", "description": "End of range in ISO 8601 format"},
                },
                "required": ["start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check available time slots for booking an appointment. Use when the user wants to schedule a meeting or consultation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "Start of range in ISO 8601 (e.g. 2026-04-01T08:00:00Z)"},
                    "end": {"type": "string", "description": "End of range in ISO 8601"},
                    "duration_minutes": {"type": "integer", "description": "Desired meeting length in minutes", "default": 60},
                },
                "required": ["start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a new appointment on the calendar. Use after confirming a time slot with the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Title of the appointment"},
                    "start": {"type": "string", "description": "Start time in ISO 8601"},
                    "end": {"type": "string", "description": "End time in ISO 8601"},
                    "description": {"type": "string", "description": "Optional notes or details"},
                    "attendee_email": {"type": "string", "description": "Optional attendee email address"},
                },
                "required": ["summary", "start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_appointment",
            "description": "Update an existing appointment (change time, title, or description).",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "The calendar event ID to update"},
                    "summary": {"type": "string", "description": "New title"},
                    "start": {"type": "string", "description": "New start time in ISO 8601"},
                    "end": {"type": "string", "description": "New end time in ISO 8601"},
                    "description": {"type": "string", "description": "New description"},
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel/delete an existing appointment from the calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "The calendar event ID to cancel"},
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_payment_link",
            "description": "Create a payment link for a service. Use when a customer wants to purchase or pay for a service. The amount should be in ZAR cents (e.g. R50,000 = 5000000). Always ask for the customer's email before creating a payment link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Name of the service being purchased"},
                    "amount": {"type": "integer", "description": "Amount in ZAR cents (e.g. R50,000 = 5000000)"},
                    "email": {"type": "string", "description": "Customer email for payment receipt"},
                    "description": {"type": "string", "description": "Optional description or notes"},
                },
                "required": ["service_name", "amount", "email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_distance",
            "description": "Calculate the distance in kilometers between the business location and a customer address. Use when a service requires onsite visit or pickup and you need to estimate travel distance. Ask the customer for their address first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_address": {"type": "string", "description": "The customer's address (street, city, country)"},
                },
                "required": ["customer_address"],
            },
        },
    },
]


def get_tool_definitions() -> List[Dict[str, Any]]:
    return TOOL_DEFINITIONS


_DISPATCH_MAP = {
    "list_calendar_events": lambda args: calendar.list_events(
        time_min=args["start"], time_max=args["end"],
        max_results=args.get("max_results", 20),
    ),
    "check_availability": lambda args: calendar.get_available_slots(
        time_min=args["start"], time_max=args["end"],
        duration_minutes=args.get("duration_minutes", 60),
    ),
    "book_appointment": lambda args: calendar.create_event(
        summary=args["summary"], start=args["start"], end=args["end"],
        description=args.get("description", ""),
        attendee_email=args.get("attendee_email"),
    ),
    "update_appointment": lambda args: calendar.update_event(
        event_id=args["event_id"],
        summary=args.get("summary"), start=args.get("start"),
        end=args.get("end"), description=args.get("description"),
    ),
    "cancel_appointment": lambda args: calendar.delete_event(
        event_id=args["event_id"],
    ),
    "create_payment_link": lambda args: payments.create_payment_link(
        amount=args["amount"],
        email=args["email"],
        service_name=args["service_name"],
        description=args.get("description", ""),
    ),
    "calculate_distance": lambda args: distance.calculate_distance(
        customer_address=args["customer_address"],
    ),
}


def dispatch_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    handler = _DISPATCH_MAP.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    try:
        return handler(arguments)
    except Exception as e:
        logger.error("Tool %s failed: %s", name, e)
        return {"error": f"Tool execution failed: {e}"}
