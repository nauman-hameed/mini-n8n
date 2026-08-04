from services.api_executor import execute_api_node
from services.ai_extractor import execute_ai_extractor
from services.google_sheets import append_order_to_sheet
from services.whatsapp_service import (
    render_reply_template,
    send_whatsapp_text,
)


def run_workflow(
    nodes: list,
    edges: list,
    trigger_context: dict | None = None,
):
    node_map = {
        node["id"]: node
        for node in nodes
    }

    start_node = next(
        (
            node
            for node in nodes
            if node.get("data", {}).get("nodeType")
            in ["start", "whatsappTrigger"]
        ),
        None,
    )

    if not start_node:
        raise ValueError(
            "No start or trigger node found in workflow."
        )

    current_node = start_node
    last_output = None
    executed_nodes = []

    while current_node:
        node_type = current_node.get(
            "data",
            {},
        ).get("nodeType")

        node_data = current_node.get("data", {})
        node_id = current_node["id"]

        executed_nodes.append(node_type)

        if node_type == "start":
            last_output = {
                "message": "Workflow started."
            }

        elif node_type == "whatsappTrigger":
            incoming_message = ""
            from_phone = ""

            if trigger_context:
                incoming_message = str(
                    trigger_context.get("message", "")
                ).strip()
                from_phone = str(
                    trigger_context.get("from_phone", "")
                ).strip()
            else:
                from_phone = str(
                    node_data.get("testPhone", "")
                ).strip()

            if not incoming_message:
                incoming_message = node_data.get(
                    "message",
                    "",
                ).strip()

            if not incoming_message:
                raise ValueError(
                    "WhatsApp Trigger message is missing."
                )

            last_output = {
                "message": incoming_message,
                "from_phone": from_phone,
            }

            if from_phone and not trigger_context:
                last_output["phone"] = from_phone

        elif node_type == "api":
            last_output = execute_api_node(
                node_data
            )

        elif node_type == "aiExtractor":
            if not last_output:
                raise ValueError(
                    "AI Order Extractor did not receive any input."
                )

            message = last_output.get(
                "message",
                "",
            )

            if not message:
                raise ValueError(
                    "Incoming WhatsApp message is missing."
                )

            from_phone = last_output.get(
                "from_phone",
                "",
            )

            extracted = execute_ai_extractor(
                message
            )

            last_output = {
                **extracted,
                "from_phone": from_phone,
            }

            if not last_output.get("phone") and from_phone:
                last_output["phone"] = from_phone

        elif node_type == "googleSheets":
            if not last_output:
                raise ValueError(
                    "Google Sheets node did not receive order data."
                )

            sheet_name = node_data.get(
                "sheetName",
                "Orders",
            ).strip()

            if not sheet_name:
                raise ValueError(
                    "Google Sheets sheet name is missing."
                )

            preserved_phone = last_output.get(
                "from_phone",
                "",
            )

            sheet_result = append_order_to_sheet(
                order_data=last_output,
                sheet_name=sheet_name,
            )

            last_output = {
                **last_output,
                "from_phone": preserved_phone,
                "google_sheets": sheet_result,
            }

        elif node_type == "whatsappReply":
            if not last_output:
                raise ValueError(
                    "WhatsApp Reply did not receive order data."
                )

            reply_template = node_data.get(
                "replyMessage",
                "Thank you {{name}}! Your order for "
                "{{items}} has been received.",
            )

            reply_message = render_reply_template(
                reply_template,
                last_output,
            )

            recipient_phone = str(
                last_output.get("from_phone", "")
                or last_output.get("phone", "")
            ).strip()

            if not last_output.get("from_phone") and last_output.get("phone"):
                print(
                    "WhatsApp Reply: using extracted phone "
                    f"{last_output.get('phone')} — set Test Phone "
                    "on WhatsApp Trigger for manual runs."
                )

            whatsapp_send = None

            if recipient_phone:
                whatsapp_send = send_whatsapp_text(
                    to_phone=recipient_phone,
                    message=reply_message,
                    phone_number_id=(
                        (trigger_context or {}).get(
                            "phone_number_id"
                        )
                    ),
                )

            last_output = {
                **last_output,
                "reply_message": reply_message,
                "whatsapp_send": whatsapp_send,
            }

            return {
                "message": (
                    "Workflow executed successfully."
                    if whatsapp_send
                    else "Workflow executed. Reply prepared "
                    "(not sent — no recipient phone)."
                ),
                "executed_nodes": executed_nodes,
                "output": last_output,
            }

        elif node_type == "stop":
            return {
                "message": "Workflow executed successfully.",
                "executed_nodes": executed_nodes,
                "output": last_output,
            }

        else:
            raise ValueError(
                f"Node type '{node_type}' is not supported yet."
            )

        next_edge = next(
            (
                edge
                for edge in edges
                if edge.get("source") == node_id
            ),
            None,
        )

        if not next_edge:
            return {
                "message": "Workflow executed successfully.",
                "executed_nodes": executed_nodes,
                "output": last_output,
            }

        next_node_id = next_edge.get("target")
        current_node = node_map.get(next_node_id)

        if not current_node:
            raise ValueError(
                "Connected node not found."
            )

    raise ValueError(
        "Workflow ended unexpectedly."
    )
