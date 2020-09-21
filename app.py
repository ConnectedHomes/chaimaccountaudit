"""Chaim Account Audit Slack application."""

from operator import itemgetter
import os

import boto3
from chalice import Chalice
from tabulate import tabulate
from urllib.parse import unquote

from chalicelib.permissions import Permissions


class SlackSendFail(Exception):
    pass


class SlackRecvFail(Exception):
    pass


class EnvFail(Exception):
    pass


class AccountNotFound(Exception):
    pass


class NoData(Exception):
    pass


app = Chalice(app_name="chaimaccountaudit")


def splitQS(req):
    """Splits query string into key value pairs."""
    try:
        r = {}
        # ensure the query string is unquoted
        qs = unquote(req)
        # split at the ampersand, returns a 1 element list if there is no &
        bits = qs.split("&")
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


def sendToSlack(respondurl, msg):
    """
    Send messages back to Slack

    :param respondurl: the url to send back to
    :param msg: the text to send
    """
    try:
        if respondurl != "ignoreme":
            if len(msg) > 0:
                params = json.dumps(output(None, msg))
                r = requests.post(respondurl, data=params)
                if 200 != r.status_code:
                    emsg = "Failed to send back to initiating Slack channel"
                    emsg += ". status: {}, text: {}".format(r.status_code, r.text)
                    raise (SlackSendFail(emsg))
    except Exception as e:
        msg = f"Send to Slack Failed: {e}"
        print(msg)
        raise


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


def listGroupMembers(group, pms):
    try:
        sql = f"""
        select u.name as name
        from
        groupusermap g, awsusers u, awsgroups f
        where
        u.id=g.userid
        and g.groupid=f.id
        and f.name='{group}';
        """
        name = 0
        rows = pms.sid.query(sql)
        return [row[name] for row in rows]
    except Exception as e:
        msg = f"Exception in listGroupMembers: {type(e).__name__}: {e}"
        print(msg)
        raise


def getAccountUsers(account, pms):
    try:
        sql = f"""
        select
        a.id as aid, a.name as aname, u.name as uname, r.name as rname, r.id as rid
        from
        useracctrolemap x, awsusers u, awsaccounts a, awsroles r
        where
        a.name='{account}'
        and u.id=x.userid
        and a.id=x.accountid
        and r.id=x.roleid
        order by u.name,r.id;
        """
        aid = 0
        aname = 1
        uname = 2
        rname = 3
        rid = 4
        fields = ["aid", "aname", "uname", "rname", "rid"]
        rows = pms.sid.query(sql)
        op = {}
        for row in rows:
            if row[uname] not in op:
                op[row[uname]] = []
            # remove CrossAccount from the role name
            rdict = {"rname": row[rname].replace("CrossAccount", "")}
            # Ensure the basic roles are the last in the sorted list of user roles
            rdict["rid"] = row[rid] * 100 if row[rid] < 101 else row[rid]
            op[row[uname]].append(rdict)
        return sortData(op)
    except Exception as e:
        msg = f"Exception in getAccountUsers: {type(e).__name__}: {e}"
        print(msg)
        raise


def sortData(rows):
    try:
        op = {}
        for name in rows:
            op[name] = sorted(rows[name], key=itemgetter("rid"))
        return op
    except Exception as e:
        msg = f"Exception in sortData: {type(e).__name__}: {e}"
        print(msg)
        raise


def padLine(line, length=4):
    try:
        while len(line) < length:
            line.append("")
        return line
    except Exception as e:
        msg = f"Exception in padLine: {type(e).__name__}: {e}"
        print(msg)
        raise


def userPermRow(row, username):
    """Turns a user row into a display list for tabulate."""
    try:
        extras = []
        line = []
        for role in row:
            if role["rid"] < 1000:
                extras.append(row["rname"])
            else:
                line.append(row["name"])
        msg = f"{username}"
        msg += "\n"
        msg += tabulate(padLine(line))
        for extra in extras:
            msg += f"\n{extra}"
        return msg
    except Exception as e:
        msg = f"Exception in userPermRow: {type(e).__name__}: {e}"
        print(msg)
        raise


def displayPermissions(users, groups):
    try:
        op = ""
        first = True
        for user in users:
            skip = False
            for group in groups:
                if user in group:
                    skip = True
            if skip:
                continue
            else:
                if first:
                    first = False
                    sep = ""
                else:
                    sep = "\n\n"
                ustr = userPermRow(users[user], user)
                op += f"{sep}{ustr}"
        return op
    except Exception as e:
        msg = f"Exception in displayPermissions: {type(e).__name__}: {e}"
        print(msg)
        raise


@app.on_sns_message(topic="chaimaccountaudit")
def doSNSReq(event):
    try:
        bodydict = splitQS(event.message)
        print(f"chaimaccountaudit rcvd: {bodydict}")
        spath = getEnvParam("SECRETPATH")
        pms = Permissions(spath)
        accountid = pms.singleField(
            "awsaccounts", "id", "name", "Name", bodydict["text"], notfoundOK=True
        )
        if accountid is None:
            msg = f"""Account {bodydict["text"]} not found."""
            sendToSlack(bodydict["response_url"], msg)
            raise AccountNotFound(msg)
        users = getAccountUsers(bodydict["text"], pms)
        sre = listGroupMembers("SRE", pms)
        security = listGroupMembers("security", pms)
        msg = displayPermissions(users, (sre, security))
        sendToSlack(bodydict["response_url"], msg)
        print(msg)
        # print(sre)
        # print(security)
        # print(users)
    except Exception as e:
        msg = f"Exception in doSNSReq: {type(e).__name__}: {e}"
        print(msg)


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
