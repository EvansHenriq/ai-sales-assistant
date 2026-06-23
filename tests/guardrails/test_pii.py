from app.guardrails.pii import redact_pii


def test_redacts_email() -> None:
    result = redact_pii("contact me at john.doe@acme.com please")
    assert "EMAIL" in result.found
    assert "john.doe@acme.com" not in result.text
    assert "[REDACTED_EMAIL]" in result.text


def test_redacts_cpf() -> None:
    result = redact_pii("meu CPF e 123.456.789-01")
    assert "CPF" in result.found
    assert "123.456.789-01" not in result.text


def test_redacts_credit_card() -> None:
    result = redact_pii("card number 4111 1111 1111 1111")
    assert "CREDIT_CARD" in result.found
    assert "4111" not in result.text


def test_redacts_phone() -> None:
    result = redact_pii("call me at +1 (555) 123-4567")
    assert "PHONE" in result.found


def test_benign_text_unchanged() -> None:
    text = "The Growth plan is great for product analytics."
    result = redact_pii(text)
    assert result.found == []
    assert result.text == text
