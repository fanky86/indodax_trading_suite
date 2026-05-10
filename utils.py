# =========================================
# utils.py
# FINAL SAFE INDODAX UTILS
# =========================================

import requests
import hmac
import hashlib
import time
import csv
import os

from colorama import Fore

from config import Config


# =========================================
# TELEGRAM
# =========================================

def send_telegram(message: str):

    if not Config.TELEGRAM_ENABLED:
        return

    try:

        url = (

            f"https://api.telegram.org/bot"

            f"{Config.TELEGRAM_BOT_TOKEN}"

            f"/sendMessage"
        )

        payload = {

            "chat_id":

            Config.TELEGRAM_CHAT_ID,

            "text":

            message
        }

        requests.post(

            url,

            json=payload,

            timeout=5
        )

    except Exception as e:

        print(
            Fore.RED +
            f"Telegram error: {e}"
        )


# =========================================
# PRIVATE API REQUEST
# =========================================

def indodax_signed_request(

    method: str,

    params: dict = None
):

    """
    Private API request
    """

    try:

        # =================================
        # API CHECK
        # =================================

        if not Config.INDODAX_API_KEY:

            print(
                Fore.RED +
                "[ERROR] API key missing"
            )

            return None

        if params is None:

            params = {}

        # =================================
        # REQUIRED PARAMS
        # =================================

        params["method"] = method

        params["nonce"] = str(
            int(time.time() * 1000)
        )

        # =================================
        # PAYLOAD
        # =================================

        payload = "&".join(

            [

                f"{k}={v}"

                for k, v

                in sorted(params.items())
            ]
        )

        # =================================
        # SIGNATURE
        # =================================

        sign = hmac.new(

            Config
            .INDODAX_SECRET_KEY
            .encode(),

            payload.encode(),

            hashlib.sha512

        ).hexdigest()

        headers = {

            "Key":

            Config.INDODAX_API_KEY,

            "Sign":

            sign
        }

        # =================================
        # REQUEST
        # =================================

        url = (
            f"{Config.INDODAX_BASE_URL}/tapi"
        )

        response = requests.post(

            url,

            data=params,

            headers=headers,

            timeout=10
        )

        # =================================
        # DEBUG RESPONSE
        # =================================

        print(

            Fore.BLUE +

            f"[API RESPONSE] "

            f"{response.text}"
        )

        return response.json()

    except Exception as e:

        print(
            Fore.RED +
            f"Signed request error: {e}"
        )

        return None


# =========================================
# GET BALANCE
# =========================================

def get_balance(coin='idr'):

    try:

        result = indodax_signed_request(
            "getInfo"
        )

        if not result:

            return {}

        if result.get("success") != 1:

            print(

                Fore.RED +

                f"[BALANCE ERROR] "

                f"{result}"
            )

            return {}

        balances = (

            result

            .get("return", {})

            .get("balance", {})
        )

        return balances

    except Exception as e:

        print(
            Fore.RED +
            f"Get balance error: {e}"
        )

        return {}


# =========================================
# PLACE ORDER
# =========================================

def place_order(

    pair: str,

    order_type: str,

    price: float,

    amount: float
):

    """
    order_type:
    buy / sell
    """

    try:

        # =================================
        # SIMULATION MODE
        # =================================

        if not Config.ALLOW_REAL_ORDER:

            print(

                Fore.CYAN +

                f"[SIMULATION] "

                f"{order_type.upper()} "

                f"{pair} "

                f"@ {price}"
            )

            return {

                "success": 1,

                "simulate": True
            }

        # =================================
        # BUY ORDER
        # =================================

        if order_type.lower() == "buy":

            params = {

                "pair": pair,

                "type": "buy",

                "price": str(price),

                "idr": str(amount)
            }

        # =================================
        # SELL ORDER
        # =================================

        else:

            params = {

                "pair": pair,

                "type": "sell",

                "price": str(price),

                "coin": str(amount)
            }

        result = indodax_signed_request(

            "trade",

            params
        )

        return result

    except Exception as e:

        print(
            Fore.RED +
            f"Place order error: {e}"
        )

        return None


# =========================================
# CANCEL ORDER
# =========================================

def cancel_order(

    pair: str,

    order_id: str,

    side: str
):

    try:

        params = {

            "pair": pair,

            "order_id": order_id,

            "type": side
        }

        result = indodax_signed_request(

            "cancelOrder",

            params
        )

        return result

    except Exception as e:

        print(
            Fore.RED +
            f"Cancel order error: {e}"
        )

        return None


# =========================================
# OPEN ORDERS
# =========================================

def get_open_orders(pair: str):

    try:

        params = {
            "pair": pair
        }

        result = indodax_signed_request(

            "openOrders",

            params
        )

        return result

    except Exception as e:

        print(
            Fore.RED +
            f"Open orders error: {e}"
        )

        return None


# =========================================
# CSV LOGGER
# =========================================

def log_to_csv(

    filename: str,

    data: dict
):

    try:

        file_exists = os.path.isfile(
            filename
        )

        with open(

            filename,

            'a',

            newline=''

        ) as f:

            writer = csv.DictWriter(

                f,

                fieldnames=data.keys()
            )

            if not file_exists:

                writer.writeheader()

            writer.writerow(data)

    except Exception as e:

        print(
            Fore.RED +
            f"CSV log error: {e}"
        )
