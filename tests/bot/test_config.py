from bot.config import BotConfig


def test_allowed_user_ids_parses_csv():
    config = BotConfig(telegram_bot_token="t", telegram_allowed_user_ids="1, 2 ,3")
    assert config.allowed_user_ids == {1, 2, 3}


def test_allowed_user_ids_empty_when_unset():
    config = BotConfig(telegram_bot_token="t", telegram_allowed_user_ids="")
    assert config.allowed_user_ids == set()
