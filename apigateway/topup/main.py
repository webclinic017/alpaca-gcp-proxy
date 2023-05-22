import time
from enum import Enum

import functions_framework
from google.cloud import firestore  # type: ignore

from infra import auth  # type: ignore


class Frequency(Enum):
    Weekly = 1
    Monthly = 2


def process(email_id: str, amount: int, frequency: Frequency) -> None:
    print(f"process: {email_id} {amount}, {frequency}")

    db = firestore.Client()

    topup_ref = db.reference("topup")
    user = topup_ref.child(email_id)
    status = user.push(
        {
            "amount": amount,
            "frequency": str(frequency),
            "create_at": time.time_ns(),
        }
    )

    print("document write status=", status)


@functions_framework.http
@auth
def topup(request):
    """Implement PUT /users/{emailId}/topup end-point"""

    email_id = request.args.get("emailId")
    print(f"Received user_id: {email_id}")

    # validate API
    payload = request.get_json() if request.is_json else None

    if (
        not payload
        or not (amount_str := payload.get("amount"))
        or not (frequency_str := payload.get("frequency"))
    ):
        return (
            "Missing or invalid payload (expected JSON w/ 'amount' and 'frequency')",
            400,
        )

    try:
        amount = int(amount_str)
        assert amount > 0
    except Exception:
        return ("amount needs to be positive int", 400)

    try:
        frequency = Frequency[frequency_str]
    except Exception:
        return ("frequency needs to be 'Weekly' or 'Monthly'", 400)

    process(email_id, amount, frequency)

    return ("OK", 200)
