###
# Author: Glitch <Glitch@Glitch.is>
# Name: InnaCLI
# Description:
#
# Report any bugs on GitHub <https://github.com/Glitch-is/InnaCLI>
###

import requests
import json
from getpass import getpass
from tabulate import tabulate
import sys
import time

global user

class User:
    def __init__(self, id, cookie):
        self.id = id
        self.cookie = cookie


def login():
    while True:
        u = input("Kennitala: ") # Prompt the user for their social security number
        p = getpass() # Prompt the user for their password wich doesn't get displayed thanks to the getpass module

        payload = {
            'Kennitala': u,
            'Lykilord': p,
            '_ROWOPERATION': 'Staðfesta'
        } # Initialize the login payload

        print("Attempting to log into inna.is")

        login = requests.post('https://www.inna.is/login.jsp', data=payload) # Login to the old Inna login system with the payload

        if("Innskráning tókst ekki" in login.text):
            print("Login Failed. Please try again...")
        else:
            print("Login Successful")
            break;

    cookie = {
        "JSESSIONID": login.cookies["JSESSIONID"]
    } # Get the Session from the response cookie to use for next step of the login

    oldInna = requests.get('https://www.inna.is/opna.jsp?adgangur=0', cookies=cookie) # Tell inna we want to use the new site so it will send us a token to skip the new inna authentication, how convienient?
    activate = oldInna.text.split("'")[1] # Parse the link to the new inna with our token

    newInna = requests.get(activate) # Activate our new session
    seshId =newInna.cookies["JSESSIONID"]
    newCookie = {
        "JSESSIONID": seshId,
        "XSRF-TOKEN": newInna.cookies["XSRF-TOKEN"]
    } # Store our new session in a cookie

    studentInfo = requests.get('https://nam.inna.is/inna11/api/UserData/GetLoggedInUser', cookies=newCookie) # Get the student info
    studentId = studentInfo.json()['studentId']  # Parse the studentId from the studentInfo
    return User(studentId, newCookie)

def updateXSRF():
    req = requests.get('https://nam.inna.is/inna11/api/UserData/GetLoggedInUser', cookies=user.cookie)
    user.cookie["XSRF-TOKEN"] = req.cookies["XSRF-TOKEN"]

def getAssignments(args):
    assignments = requests.get('https://nam.inna.is/inna11/api/GetAssignments/GetStudentAssignments?control=0&group_id=&module_id=&order=0&type=', cookies=user.cookie)
    print(assignments.cookies["XSRF-TOKEN"])
    print(tabulate([[x["assignmentId"], x["module"], x["name"], x["handInFullDate"], "Yes" if x["handedIn"] is "1" else "No"] for x in assignments.json()], ["ID", "Class", "Name", "Hand In", "Turned In"]))

def getAssignment(args):
    assId = args[0]
    assignment = requests.get('https://nam.inna.is/inna11/api/GetAssignments/GetStudentAssignmentsById?assignmentId='+assId+'&studentId='+user.id, cookies=user.cookie).json()
    print(assignment["moduleName"] + ' - ' + assignment["name"] + ' | ' + assignment["handInFullDate"])
    print("Description:")
    print(assignment["description"])
    print("Attachments:")
    attachments = requests.get('https://nam.inna.is/inna11/api/Attachment/GetProjectAttachments?projectId=' + assignment["projectId"], cookies=user.cookie).json()
    print(tabulate([[x["attachmentId"], x["fileName"] ] for x in attachments], ["ID", "File Name"]))
    turnedIn = requests.get('https://nam.inna.is/inna11/api/Attachment/GetAssignmentAttachments?assignmentId='+assId+'&studentId=' + user.id, cookies=user.cookie)
    if turnedIn.text:
        print("Turned In Files:")
        print(tabulate([[x["attachmentId"], x["fileName"]] for x in turnedIn.json()], ["ID", "File Name"]))

def deleteAssignment(args):
    assId = args[0]
    requests.delete('https://nam.inna.is/inna11/api/Attachment/DeleteAttachment?attachmentId=' + assId, cookies=user.cookie)

def download(args):
    attachId = args[0]
    r = requests.get("https://nam.inna.is/inna11/api/Attachment/DownloadAttachment/"+attachId+"/2?student=1", cookies=user.cookie, stream=True)
    filename = r.headers["content-disposition"].split(" = ")[1][1:-1]
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    print(filename + " Downloaded")

def submit(args):
    updateXSRF()
    assignId, filename = args[0], " ".join(args[1:])
    payload = {
        'assignmentId': assignId,
        'gradePublished': 1,
        'handIn': 1,
        'handInDate': time.strftime("%d.%m.%Y %H:%M"),
        'members': [],
        'taskOrderCount': "0",
        'tasks': [],
        'type': "0"
    }
    print(user.cookie)
    sub = requests.post('https://nam.inna.is/inna11/api/GetAssignments/SubmitStudentAssignment', cookies=user.cookie, files={'file':open(filename, 'rb')}, data=payload)
    print(sub.text)
    print(sub.headers)

def help(args):
    print("ass - list of open assignments")
    print("desc <assignmentId> - description for assignment")
    print("download <attachmentId> - download attachment")
    print("submit <assignmentId> <file> - turn in assignment")
    print("delete <assignmentId> - delete turned in assignment")

def quit(args):
    sys.exit(0)

commands = {"ass": getAssignments,
            "desc": getAssignment,
            "download": download,
            "submit": submit,
            "delete": deleteAssignment,
            "help": help,
            "quit": quit}

print("'help' for list of commands")
user = login()
while True:
    print(">", end="")
    inp = input().split()
    commands[inp[0]](inp[1:])
