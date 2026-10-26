from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=7,
        ),
        text="answer",
    )

    class Chat:
        def send_message(self, message):
            return response

    assert ask_module.ask("question", Chat()) == "answer"
    assert capsys.readouterr().out == "[トークン数] 入力: 12, 出力: 7\n"


def test_main_keeps_chat_history_for_follow_up_questions(monkeypatch, capsys):
    sent_messages = []
    create_calls = []

    class Chat:
        def send_message(self, message):
            sent_messages.append(message)
            return SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=10,
                    candidates_token_count=5,
                ),
                text=f"answer to {message}",
            )

    chat = Chat()

    class Chats:
        def create(self, *, model):
            create_calls.append(model)
            return chat

    class Client:
        def __init__(self, *, api_key):
            self.chats = Chats()

    monkeypatch.setattr(ask_module.genai, "Client", Client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module, "MODEL", "test-model")
    monkeypatch.setattr(
        "sys.argv", ["app.ask", "first question"]
    )
    responses = iter(["follow-up question", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    ask_module.main()

    output = capsys.readouterr().out
    assert sent_messages == ["first question", "follow-up question"]
    assert create_calls == ["test-model"]
    assert "answer to first question" in output
    assert "answer to follow-up question" in output
