#!/usr/bin/env python

import trello
import smtplib
import sqlite3
import datetime
import sys
import os

execfile(os.path.abspath(os.path.dirname(sys.argv[0])) + "/trollo-secret.py")

trelloClient = trello.TrelloClient(api_key=trelloApiKey,
                                   api_secret=trelloApiSecret,
                                   token=trelloToken,
                                   token_secret=trelloTokenSecret)
boards = trelloClient.list_boards()
treadwheelBoard = [b for b in boards if b.name == "Treadwheel"][0]
treadwheelLabels = treadwheelBoard.get_labels()
treadwheelLists = treadwheelBoard.open_lists()
doneList = treadwheelLists[0]
todoList = treadwheelLists[1]
todayList = treadwheelLists[2]
tasksBoard = [b for b in boards if b.name == "Tasks"][0]
tasksLists = tasksBoard.all_lists()

# generate up to MAX_DUMMY_CARDS dummy tasks
MAX_DUMMY_CARDS = 10
dummyGeneratorList = [l for l in tasksLists if l.name == "automatic dummy generator"][0]
nDummyCards = len(dummyGeneratorList.list_cards())
nDummyCardsToGenerate = MAX_DUMMY_CARDS - nDummyCards
for i in range(nDummyCardsToGenerate):
    newDummyCard = dummyGeneratorList.add_card("to be renamed")
    newDummyCard.fetch()
    newDummyCard._set_remote_attribute('name', str(newDummyCard.short_id) + ' ')

# get yesterday's date
todayListName = todayList.name
todayListNameParenthesisPosition = todayListName.find('(')
year = int(todayListName[todayListNameParenthesisPosition+1:todayListNameParenthesisPosition+5])
month = int(todayListName[todayListNameParenthesisPosition+6:todayListNameParenthesisPosition+8])
day = int(todayListName[todayListNameParenthesisPosition+9:todayListNameParenthesisPosition+11])
todayDate = datetime.datetime(year, month, day)
yesterdayDate = todayDate - datetime.timedelta(days=1)

# delete cards in the Done list and insert them into the database
dbPath = os.path.abspath(os.path.dirname(sys.argv[0])) + "/timetrack.db"
con = sqlite3.connect(dbPath, detect_types=sqlite3.PARSE_DECLTYPES)
cur = con.cursor()
with con:
    for card in doneList.list_cards():
        card.fetch()
        spacePosition = card.name.find(" ")
        if spacePosition == -1:
            taskId = card.name[:]
        else:
            taskId = card.name[:spacePosition]
        if card.labels:
            duration = int(card.labels[0].name[0])
            cur.execute("INSERT INTO Sessions(Date, TaskId, Duration) VALUES (?, ?, ?);", (yesterdayDate, taskId, duration))
        card.delete()

# move cards from today's list to Todo list
for card in todayList.list_cards():
    card.change_list(todoList.id)

# move today's list to the end and change the date to next week
trelloClient.fetch_json('/lists/' + todayList.id + '/pos',
                        http_method='PUT',
                        post_args={'value': 'bottom', })
nextWeekDate = todayDate + datetime.timedelta(days=7)
todayListName = todayListName[:todayListNameParenthesisPosition] + '(' + nextWeekDate.strftime("%Y-%m-%d") + ')'
todayList._set_remote_attribute('name', todayListName)
ankiCard = todayList.add_card('109 anki')
ankiCard.add_label(treadwheelLabels[0])
todayList.add_card('work')
todayList.add_card('reward')
