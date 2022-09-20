from bottle import default_app, route, request, run, post, redirect
import json
import smtplib, ssl
import os
from datetime import date, timedelta
import traceback
from flask import send_from_directory, Flask, current_app


class CalendarOrganiser():
    def __init__(self):
        self.scriptDir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isdir(self.scriptDir+'/events/'):
            os.mkdir(self.scriptDir+'/events/', 0o666)


    def newEvent(self, eventName, startDate, endDate):
        start = startDate.split("-")
        end = endDate.split("-")

        sD = date(int(start[0]), int(start[1]), int(start[2]))
        eD = date(int(end[0]), int(end[1]), int(end[2]))

        delta = eD-sD

        #days between start and end
        daysLst = []
        for i in range(delta.days + 1):
            day = sD + timedelta(days=i)
            tempLst = []
            # stupid date to list converter
            for i in day.strftime("%Y-%m-%d").split("-"):
                tempLst.append(i)
            daysLst.append(tempLst)

        print(daysLst)

        mainDic = {
            "DaysList" : daysLst,
            "Availability" : {}
            }

        with open(self.scriptDir+'/events/'+eventName+'.calorgevent', 'w') as outfile:
            json.dump(mainDic, outfile, indent = '\t')


    def delEvent(self, eventName):
        os.remove(str(eventName)+'.calorgevent')


    def newAvailability(self, eventName, userName, userAvailability):
        event = json.load(open(self.scriptDir+'/events/'+str(eventName)+'.calorgevent', 'r'))
        event["Availability"][str(userName)] = userAvailability
        with open(self.scriptDir+'/events/'+eventName+'.calorgevent', 'w') as outfile:
            json.dump(event, outfile, indent = '\t')


    def delAvailability(self, eventName, userName):
        event = json.load(open(self.scriptDir+'/events/'+str(eventName)+'.calorgevent', 'r'))
        event["Availability"].pop(userName)
        with open(self.scriptDir+'/events/'+eventName+'.calorgevent', 'w') as outfile:
            json.dump(event, outfile, indent = '\t')


    def events(self):
        eventFiles = os.listdir(self.scriptDir+'/events')
        existingEvents = []
        for i in eventFiles:
            if i.split(".")[1] == "calorgevent":
                existingEvents.append(i.split(".")[0])
        return existingEvents


    def event(self, eventName):
        event = json.load(open(self.scriptDir+'/events/'+str(eventName)+'.calorgevent', 'r'))
        return event


    def eventNameAllowed(self, eventName):
        # existing events
        eventFiles = os.listdir(self.scriptDir+'/events')
        existingEvents = []
        for i in eventFiles:
            if i.split(".")[1] == "calorgevent":
                existingEvents.append(i.split(".")[0])

        # name of event
        allowedLetters = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM-1234567890"
        nameAllowed = True
        for i in eventName:
            if i not in allowedLetters:
                nameAllowed = False
        if eventName in existingEvents:
            nameAllowed = False

        return nameAllowed


    def userNameAllowed(self, userName):
        allowedLetters = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM 1234567890"
        nameAllowed = True
        for i in userName:
            if i not in allowedLetters:
                nameAllowed = False

        return nameAllowed


    def splitDaysToWeeks(self, daysList):
        weeks = []
        week = {}
        for i in daysList:
            day = date(int(i[0]), int(i[1]), int(i[2]))
            if day.weekday() == 0 and not week == {}:
                weeks.append(week)
                week = {}
            week[str(day.weekday())] = day
        if not week == {}:
            weeks.append(week)
        return weeks
        
    
    def eventLinks(self):
        global mainLink
        html = ""
        for i in self.events():
            html += "<a href="+mainLink+"/calendar-organiser/event/"+i+">"+i+"</a><br><br>"
        return html



mainLink = 'http://junm.pythonanywhere.com'
pydir = "/home/JunM/mysite"
maincss = open(pydir+'/main.css', 'r').read()
template = open(pydir+'/template.html', 'r').read()


@route('/calendar-organiser/main.css')
def calOrgCSS():
    
    return open(pydir+'/main.css', 'r').read()


@route('/calendar-organiser')
def calOrg():
    global mainLink
    
    form = '<br><form action="/calendar-organiser/addEvent" method = "post">'

    form += '<label for="eventName">New event (cannot contain special characters except dashes): </label><br>'
    form += '<input type="text" id="eventName" name="eventName" value="" required><br>'

    form += '<label for="startDate">Start date (YYYY-MM-DD): </label><br>'
    form += '<input type="text" id="startDate" name="startDate" value="" required><br>'

    form += '<label for="endDate">End date (YYYY-MM-DD): </label><br>'
    form += '<input type="text" id="endDate" name="endDate" value="" required><br>'

    form += '<input type="submit" value="Submit"></form>'


    c = CalendarOrganiser()
    html = template.format(title = "Calendar Organiser", head = "", events = c.eventLinks(), main = form, body = "")
    
    return html


@post('/calendar-organiser/addEvent', method = "post")
def calOrgAddEvent():
    with open("error.txt", "w") as log:
        try:
            c = CalendarOrganiser()
            formData = request.forms

            eventName = str(formData["eventName"])
            startDate = str(formData["startDate"])
            endDate = str(formData["endDate"])
            if not c.eventNameAllowed(eventName):
                html = '<html><head><title>Event name invalid</title></head><body><h1>Event name invalid</h1></body></html>'
                return html
            else:
                c.newEvent(eventName, startDate, endDate)
                return calOrgEvent(eventName)
        except Exception:
            traceback.print_exc(file=log)


@route('/calendar-organiser/event/<eventName>')
def calOrgViewEvent(eventName = ''):
    return calOrgEvent(str(eventName))


def calOrgEvent(eventName):
    with open("error.txt", "w") as log:
        try:
            global mainLink
            html = "<h1>"+eventName+"</h1>"
            c = CalendarOrganiser()
            event = c.event(eventName)
            html += '<form action="/calendar-organiser/event/'+eventName+'/addAvail" method = "post">'
            isMobile = False
            if isMobile:
                for i in range(len(event["DaysList"])):
                    tempList = event["DaysList"][i]
                    html += "<br>"
                    html += "<h2>"+tempList[0]+"-"+tempList[1]+"-"+tempList[2]+"</h2>"

                    html += '<div style="line-height: 0.3;">'
                    availForm = ['Unavailable', 'Maybe unavailable', 'Available']
                    availCol = ['red', 'blue', 'green']
                    for j in event["Availability"]:
                        availInt = event["Availability"][j][i]
                        avail = availForm[availInt]
                        html += '<p style="color:'+availCol[availInt]+'">'+j+': '+avail+'</p>'
                    html += "</div><br><div>"

                    for j in range(3):
                        inputId = str(i)+'-'+str(j)
                        html += '<input type="radio" id="'+inputId+'" name="'+str(i)+'" value="'+str(j)+'" required>'
                        html += '<label for="'+inputId+'">'+availForm[j]+'</label><br>'
                    html += "</div>"
            else:
                weeks = c.splitDaysToWeeks(event["DaysList"])
                with open("weeks.txt", "w") as f:
                    f.write(str(weeks))
                html += '<table style="border-spacing: 10px 0;">'
                for i in weeks:
                    html += '<tr>'
                    for j in range(7):
                        if str(j) in i:
                            html += '<td>'

                            html += "<br>"

                            # stupid date to list converter
                            day = []
                            for k in i[str(j)].strftime("%Y-%m-%d").split("-"):
                                day.append(k)

                            html += "<h2>"+day[0]+"-"+day[1]+"-"+day[2]+"</h2>"

                            dayIndex = event["DaysList"].index(day)

                            html += '<div style="line-height: 0.3;">'
                            availForm = ['Unavailable', 'Perchance', 'Available']
                            availCol = ['red', 'blue', 'green']
                            for k in event["Availability"]:
                                availInt = event["Availability"][k][dayIndex]
                                avail = availForm[availInt]
                                html += '<p style="color:'+availCol[availInt]+'">'+k+': '+avail+'</p>'
                            html += "</div><br><div>"

                            for k in range(3):
                                inputId = str(dayIndex)+'-'+str(k)
                                #availList = list(event["Availability"])
                                #availInt = event["Availability"][availList[k]][dayIndex]
                                #if k == availInt:
                                #    html += '<input type="radio" id="'+inputId+'" name="'+str(dayIndex)+'" value="'+str(k)+'" required checked = "checked">'
                                #else:
                                #    html += '<input type="radio" id="'+inputId+'" name="'+str(dayIndex)+'" value="'+str(k)+'" required>'
                                html += '<input type="radio" id="'+inputId+'" name="'+str(dayIndex)+'" value="'+str(k)+'" required>'
                                html += '<label for="'+inputId+'">'+availForm[k]+'</label><br>'
                            html += "</div>"

                            html += '</td>'
                        else:
                            html += '<td>'
                            html += '</td>'
                    html += '</tr>'
                html += '</table>'

            html += "<br>"

            html += '<label for="unm">Name: (No special characters)</label><br>'
            html += '<input type="text" id="unm" name="unm" value="" required><br>'

            html += '<input type="submit" value="Submit"></form>'
            return template.format(title = eventName, head = "", events = c.eventLinks(), main = html, body = "")
        except Exception:
            traceback.print_exc(file=log)


@post('/calendar-organiser/event/<eventName>/addAvail', method = "post")
def calOrgAddAvail(eventName = ''):
    with open("error.txt", "w") as log:
        try:
            formData = request.forms
            c = CalendarOrganiser()
            unm = formData['unm']
            if not c.userNameAllowed(unm):
                html = '<html><head><title>User name invalid, must not contain special characters</title></head><body><h1>User name invalid, must not contain special characters</h1></body></html>'
                return html
            else:
                formData.pop('unm')
                userAvail = []
                for i in formData:
                    userAvail.append(int(formData[i]))
                c.newAvailability(eventName, unm, userAvail)
                return calOrgEvent(eventName)
        except Exception:
            traceback.print_exc(file=log)


#@route('/favicon.ico')
#def favicon():
#    with application.app_context():
#        return send_from_directory(os.path.join(application.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')


application = default_app()