import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Dict, Any, Tuple
from app.core.config import settings


class TelegramAuthService:
    @staticmethod
    def validate_init_data(init_data: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates Telegram Mini App initData server-side.
        Returns (is_valid, user_data_dict).
        In development/demo mode with dummy tokens, allows graceful fallback for test environments.
        """
        # In development mode, allow seamless local browser testing without Telegram wrapper
        if settings.APP_ENV == "development":
            if not init_data or init_data == "demo_init_data" or "hash=" not in init_data:
                return True, {"id": 999999999, "first_name": "Demo Listener", "username": "demouser"}

        if not init_data:
            return False, {}

        try:
            parsed = urllib.parse.parse_qs(init_data)
            data_dict = {k: v[0] for k, v in parsed.items()}

            if "hash" not in data_dict:
                return False, {}

            received_hash = data_dict.pop("hash")

            # Check if auth_date is present and fresh
            auth_date = int(data_dict.get("auth_date", 0))
            current_time = int(time.time())
            if current_time - auth_date > settings.TELEGRAM_INITDATA_MAX_AGE_SECONDS:
                # Expired
                return False, {}

            # Construct data check string
            check_keys = sorted(data_dict.keys())
            data_check_string = "\n".join(f"{k}={data_dict[k]}" for k in check_keys)

            # Compute secret key
            # WebAppData secret key per official Telegram specification:
            secret_key = hmac.new(b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()
            computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

            # For development test suite or mock tokens:
            if settings.APP_ENV == "development" and settings.TELEGRAM_BOT_TOKEN == "demo_bot_token":
                user_raw = data_dict.get("user")
                if user_raw:
                    return True, json.loads(user_raw)
                return True, {"id": 999999999, "first_name": "Demo", "username": "demouser"}

            is_valid = hmac.compare_digest(computed_hash, received_hash)
            if not is_valid:
                return False, {}

            user_raw = data_dict.get("user")
            user_data = json.loads(user_raw) if user_raw else {}
            return True, user_data

        except Exception:
            return False, {}


telegram_auth_service = TelegramAuthService()
