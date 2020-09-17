"""Chaim Account Audit Slack application."""

from chalice import Chalice
from urllib.parse import unquote

from chalicelib.permissions import Permissions


class SlackSendFail(Exception):
    pass


class SlackRecvFail(Exception):
    pass


app = Chalice(app_name="chaimaccountaudit")


def splitQS(req):
    """Splits query string into key value pairs."""
    r = {}
    # ensure the query string is unquoted
    qs = unquote(req)
    # split at the ampersand, returns a 1 element list if there is no &
    bits = req.split("&")
    for bit in bits:
        # split into key/value
        k, v = bit.split("=")
        # strip external whitespace/newlines from
        # key and value and store in dictionary
        r[k.strip()] = v.strip()
    return r


@app.route("/", methods=["POST"], content_types=["application/x-www-form-urlencoded"])
def chaimaccountaudit():
    try:
        # the raw body string in the request from slack
        reqbody = app.current_request.raw_body.decode()
        # split the body apart into key value pairs
        bodydict = splitQS(reqbody)
        # fail if not a valid request from slack
        if "text" not in bodydict:
            raise SlackRecvFail(f"text key not sent by Slack\nbodydict: {bodydict}")
        account = bodydict["text"]
    except Exception as e:
        msg = f"Exception in chaimaccountaudit: {type(e).__name__}: {e}"
        print(msg)
        raise
