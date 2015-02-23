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

    cookie = {"JSESSIONID": login.cookies["JSESSIONID"]} # Get the Session from the response cookie to use for next step of the login

    oldInna = requests.get('https://www.inna.is/opna.jsp?adgangur=0', cookies=cookie) # Tell inna we want to use the new site so it will send us a token to skip the new inna authentication, how convienient?
    activate = oldInna.text.split("'")[1] # Parse the link to the new inna with our token

    newInna = requests.get(activate) # Activate our new session
    seshId =newInna.cookies["JSESSIONID"]
    newCookie = {"JSESSIONID": seshId} # Store our new session in a cookie

    studentInfo = requests.get('https://nam.inna.is/inna11/api/UserData/GetLoggedInUser', cookies=newCookie) # Get the student info
    studentId = studentInfo.json()['studentId']  # Parse the studentId from the studentInfo
    return User(studentId, newCookie)

def getAssignments(args):
    assignments = requests.get('https://nam.inna.is/inna11/api/GetAssignments/GetStudentAssignments?control=0&group_id=&module_id=&order=0&type=', cookies=user.cookie).json()
    print(tabulate([[x["assignmentId"], x["module"], x["name"], x["handInFullDate"]] for x in assignments], ["ID", "Class", "Name", "Hand In"]))

def getAssignment(args):
    assId = args[0]
    assignment = requests.get('https://nam.inna.is/inna11/api/GetAssignments/GetStudentAssignmentsById?assignmentId='+assId+'&studentId='+user.id, cookies=user.cookie).json()
    print(assignment["moduleName"] + ' - ' + assignment["name"] + ' | ' + assignment["handInFullDate"])
    print("Description:")
    print(assignment["description"])
    print("Attachments:")
    attachments = requests.get('https://nam.inna.is/inna11/api/Attachment/GetProjectAttachments?projectId=' + assignment["projectId"], cookies=user.cookie).json()
    print(tabulate([[x["attachmentId"], x["fileName"] ] for x in attachments], ["ID", "File Name"]))

def help(args):
    print("assignments - list of open assignments")
    print("assignment <assignmentId> - info of assignment")
    print("download <attachmentId> - downloads attachment")

commands = {"assignments": getAssignments,
            "assignment": getAssignment}

print("'help' for list of commands")
user = login()
while True:
    print(">", end="")
    inp = input().split()
    commands[inp[0]](inp[1:])
