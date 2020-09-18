"""Chaim Account Audit Slack application."""

import os

import boto3
from chalice import Chalice
from urllib.parse import unquote

from chalicelib.permissions import Permissions


class SlackSendFail(Exception):
    pass


class SlackRecvFail(Exception):
    pass


class EnvFail(Exception):
    pass


app = Chalice(app_name="chaimaccountaudit")


def splitQS(req):
    """Splits query string into key value pairs."""
    try:
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
    except Exception as e:
        msg = f"Exception in splitQS: {type(e).__name__}: {e}"
        print(msg)
        raise


def getEnvParam(param):
    try:
        val = os.environ.get(param, "wibble")
        if val == "wibble":
            raise EnvFail(f"The '{param}' key not set in the environment.")
        return val
    except Exception as e:
        msg = f"Exception in getEnvParam: {type(e).__name__}: {e}"
        print(msg)
        raise


def publishToSNS(topicarn, snsmsg):
    try:
        sns = boto3.client("sns")
        sns.publish(TopicArn=topicarn, Message=snsmsg)
    except Exception as e:
        msg = f"Exception in publishToSNS: {type(e).__name__}: {e}"
        print(msg)
        raise


@app.lambda_function
def doSNSReq():
    try:
        pass
    except Exception as e:
        msg = f"Exception in doSNSReq: {type(e).__name__}: {e}"
        print(msg)


def output(err, res=None, attachments=None):
    """Build the output string to return to slack."""
    try:
        ret = {
            "response_type": "ephemeral",
            "statusCode": "400" if err else "200",
            "text": f"{err}" if err else f"{res}",
            "headers": {"Content-Type": "application/json"},
        }
        if attachments is not None:
            ret["attachments"] = makeAttachments(attachments)
        return ret
    except Exception as e:
        msg = f"Exception in output: {type(e).__name__}: {e}"
        print(msg)
        raise


def makeAttachments(attachments, pretext=None):
    try:
        ret = [
            {
                "pretext": f"{pretext}",
                "text": f"{attachments}",
                "mrkdwn_in": ["text", "pretext"],
            }
        ]
        return ret
    except Exception as e:
        msg = f"Exception in makeAttachments: {type(e).__name__}: {e}"
        print(msg)
        raise


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
        # hand off to SNS as slack requires that this function returns within 3 seconds.
        snstopic = getEnvParam("SNSTOPICARN")
        publishToSNS(snstopic, reqbody)
        return output(None, "Please wait...")
    except Exception as e:
        msg = f"Exception in chaimaccountaudit: {type(e).__name__}: {e}"
        print(msg)
        return output(msg)
