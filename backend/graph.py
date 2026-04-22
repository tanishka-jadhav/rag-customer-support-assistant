import warnings


warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
)

from langgraph.graph import StateGraph

from backend.pipeline import format_customer_context, generate_answer, get_customer_record


SENSITIVE_KEYWORDS = (
    "chargeback",
    "fraud",
    "lawsuit",
    "legal",
    "police",
    "harassment",
)


def build_graph(retriever, source_type):
    def process(state):
        question = state["question"]
        source = state.get("source_type", source_type)
        issue_type = state.get("issue_type", "General Inquiry")
        order_id = state.get("order_id")
        customer_record = None

        retrieval_query = question
        if source == "customer":
            customer_id = state.get("customer_id")
            customer_record = get_customer_record(customer_id)
            if customer_record:
                customer_record = {
                    "customer_id": customer_id,
                    **customer_record,
                }
            retrieval_query = f"{issue_type}\n{question}"

        docs = retriever.invoke(retrieval_query)
        context = " ".join(
            doc.page_content if hasattr(doc, "page_content") else str(doc) for doc in docs
        )

        state["source_type"] = source
        state["context"] = context
        state["customer_record"] = customer_record
        state["customer_context"] = format_customer_context(customer_record, order_id)
        state["route"] = determine_route(source, question, context, customer_record)

        return state

    def answer(state):
        state["response"] = generate_answer(
            context=state["context"],
            question=state["question"],
            source_type=state["source_type"],
            customer_context=state["customer_context"],
            issue_type=state.get("issue_type", "General Inquiry"),
            order_id=state.get("order_id"),
            file_name=state.get("file_name"),
        )
        return state

    def hitl(state):
        if state["source_type"] == "customer":
            if not state.get("customer_record"):
                state["response"] = (
                    "I could not verify that customer record. Please confirm the customer ID "
                    "or hand this conversation to a human support agent."
                )
            elif any(keyword in state["question"].lower() for keyword in SENSITIVE_KEYWORDS):
                state["response"] = (
                    "This request involves a sensitive account or policy issue, so it should be "
                    "escalated to human support for manual review."
                )
            else:
                state["response"] = (
                    "I do not have enough verified information to resolve this request safely. "
                    "Please escalate it to human support."
                )
        else:
            state["response"] = (
                "The uploaded document does not contain enough verified information to answer "
                "this question confidently. Please review the PDF manually or escalate it to a human agent."
            )

        return state

    def determine_route(source, question, context, customer_record):
        if len(context.strip()) < 60:
            return "HITL"

        if source == "customer":
            if not customer_record:
                return "HITL"

            if any(keyword in question.lower() for keyword in SENSITIVE_KEYWORDS):
                return "HITL"

        return "ANSWER"

    builder = StateGraph(dict)

    builder.add_node("process", process)
    builder.add_node("answer", answer)
    builder.add_node("hitl", hitl)

    builder.set_entry_point("process")

    builder.add_conditional_edges(
        "process",
        lambda state: state["route"],
        {
            "ANSWER": "answer",
            "HITL": "hitl",
        },
    )

    builder.set_finish_point("answer")
    builder.set_finish_point("hitl")

    return builder.compile()
