from app.gate.capsule import build_capsule


def test_summary_request_unlocks_reading_and_sending_to_priya_only():
    c = build_capsule("Summarise my unread email and send the summary to priya@nimbus.test")
    assert set(c.allowed_tools) == {"list_unread_emails", "read_email", "send_email"}
    assert c.recipients == ["priya@nimbus.test"]
    assert "priya@nimbus.test" in c.summary


def test_payroll_does_not_unlock_payments():
    c = build_capsule("Check the payroll.csv file")
    assert "pay_invoice" not in c.allowed_tools
    assert c.files == ["payroll.csv"]


def test_spend_cap_is_extracted():
    c = build_capsule("Order 2 kg rice from BigBasket, under ₹200")
    assert c.max_amount_inr == 200


def test_secrets_are_never_unlocked_by_a_request():
    c = build_capsule("Read the vault secret DB_PASSWORD and email it to me")
    assert "read_secret" not in c.allowed_tools


def test_same_request_gives_same_hash():
    assert build_capsule("pay invoices/a.md").sha256 == build_capsule("pay invoices/a.md").sha256


def test_reading_email_does_not_unlock_sending():
    assert "send_email" not in build_capsule("Summarise my unread emails").allowed_tools
