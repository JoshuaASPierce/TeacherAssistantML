#Minimum Viable Product:

import pickle #Pickle is a built in python lib that handles our file saving and loading
import math #Math allows for a few trickier bits of our algorithm to be simplified with the built in lib
#Kivy is a GUI library
from kivy.app import App #Kivy.app is the root for the applications gui
from kivy.lang import Builder #Builder lets the program load an external .kv file for use by kivy, which is a simpler way to code kivy gui widgets
from kivy.uix.screenmanager import ScreenManager, Screen, CardTransition #The screen manager helps our program go from one screen to another
from kivy.uix.textinput import TextInput #Text input is what it says: It is a widget which handles text being inputed in the GUI
from kivy.uix.popup import Popup #kivy.popup handles any popup windows we need (Specifically used for the study screen and the report generator)
from kivy.uix.label import Label #A label is a simple text box. This isn't used much on this side of the application, just for the hard coded popup boxes
import os #Used for handling paths for files
import random as r #A built in lib for generating random numbers. Used once for choosing where to place answers in the Study screen

defaultElo = 1000 #The default elo score
kValue = 50 #The "Pot" of points the players are playing for. 
currentQuestionPool = [] #The pool of questions currently loaded for the user
currentSetName = '' #The name of the current pool of questions
cQI = 0 #The current question's index number. Defaults to 0
questionPoolMem = 5 #The number of questions that can be kept in previous questions
kvFileName = 'kivyMarkupV1.kv' #The name of the .kv file to be loaded
startingFileFolder = '~/Documents'

class Question:
    def __init__(self, id, question, possAns, corAns, elo):
        self.id = id #A unique ID provided at time of question creation
        self.question = question #A string of the question to be posed
        self.possAns = possAns #A list of possible answers as strings
        self.corAns = corAns #The correct answer, as a string
        self.elo = elo #A score to help determine a questions difficulty based on the elo ranking system

class User:
    def __init__(self, id, name):
        self.id = id #A unique ID given at creation
        self.name = name #A non unique name of the user
        self.elo = defaultElo #A score to help determine the current questions the user will go against
        self.previousQuestions = [] #A list of ids of the previous 20 questions answered

currentUser = User(1, 'n/a') #Defines a blank current user

#Calculates the probability of a user succeding per the Elo ranking system.
def calcProb(rA, rB): 
    return 1.0 / (1.0 + math.pow(10, ((rB - rA)/400)))

#Given a winner and a loser of a 'match', change the elo scores appropriately
def eloChange(winner, loser): 
    pWin = calcProb(loser.elo, winner.elo) #Calculate the probability of the winner having won
    pLose = calcProb(winner.elo, loser.elo) #Calculate the loser's chances
    #Elo's equation: R(a) = a + K * (S - P), R(a) is the resulting score, a is the score, K is the "Pot", S is some number between 0 and 1 for how well the 'player' did, and P is the probability of winning
    winner.elo = winner.elo + kValue * (1 - pWin) #Change the winners score equal to the elo equation given
    loser.elo = loser.elo + kValue * (0 - pLose) #Change the losers score equal to the given elo equation

#Given a user, find the question closest to them in elo that is not on their list
def matchMaking(user): 
    closest = Question(0, "Test", "N/a", "N/a", 100000) #Starting question will be a test question not used elsewhere
    for each in currentQuestionPool: #For each question in the current pool of questions
        if each.id not in user.previousQuestions: #If the question is not currently in the list of the user's previously answered questions
            if abs(each.elo - user.elo) < abs(closest.elo - user.elo): #If the difference between this question and the users elo are smaller than the next closest, then this is now the closest
                closest = each
    try:
        return currentQuestionPool.index(closest) #return the closest question in elo
    except:
        return "None" #If there are no questions in the question pool, or if there is an issue finding the closest, return none

#Finds an ID not used in the current question pool
def newId():
    x = 1 #Temp value to hold ID's. Defaults to 1, as the lowest id available
    y = True
    while y:
        z = x
        for each in currentQuestionPool: #For each question,
            if each.id == x: #If there is an ID for the current id already:
                x += 1 #Increment the number
        if z == x: 
                y = False #If the number hasnt been incremented yet, leave the while loop
    return x #Return the ID number

#Given a rating between one and five return a number between 500 and 1500
#This is used at assignment of the question's elo value. 
def getEloFromRating(rating):
    if rating == 1:
        return 500
    elif rating == 2:
        return 750
    elif rating == 3:
        return 1000
    elif rating == 4:
        return 1250
    elif rating == 5:
        return 1500
    else:
        return 1000

#This loads the .kv file used. The file must be in the same folder as the executable/code. 
#If it is not, a path must be given as an argument.
Builder.load_file(kvFileName)

#This sections starts the 'screens' used in the GUI. 
#Each class is an individual screen.

#This screen is the Dialog opened when you are loading a new user. 
#It includes a file explorer that only shows files ending in .u (The user type files)
#It also includes a function that loads a new current user based on the selection made in the file
class LoadUDialog(Screen):
    #Start the path for the file explorer in the given folder.
    path = os.path.expanduser(startingFileFolder) 
    #Load a new user per the file explorers selection
    def load(self, selection): 
        global currentUser
        currentUser = pickle.load(open(selection, 'rb'))

#This screen is the dialog opened when you want to save a user for later use
#It includes a file explorer that shows files ending in .u
#The save function inside automatically checks to see if you are overwriting a file or not and acts accordingly
class SaveUDialog(Screen):
    #Start the path for the file explorer in the given folder.
    path = os.path.expanduser(startingFileFolder)
    #The save function takes a path and filename and saves the current user at that path.
    def save(self, path, filename):
        global currentUser
        if filename != None and '.u' in filename[-2:]: #If the filename is not empty and ends in .u
            #Save the file without an added extension (as it already has one)
            with open(os.path.join(path, filename), 'wb') as f:
                pickle.dump(currentUser, f)
        else: #Otherwise, just save the file with the extension added
            with open(os.path.join(path, filename + '.u'), 'wb') as f:
                pickle.dump(currentUser, f)

#This is the dialog opened when questions need to be loaded
#It includes a load function that loads the requested .q file
#It also sets the name of the currently selected set of questions
class LoadQDialog(Screen):
    #Start the path for the file explorer in the given folder.
    path = os.path.expanduser(startingFileFolder)
    #Load .q file per selection
    def load(self, selection):
        global currentQuestionPool, currentSetName
        currentQuestionPool = pickle.load(open(selection, 'rb'))
        currentSetName = selection

#This is the dialog used to save Question sets for later use.
#It includes a file explorer that shows files ending in .q
#The save function inside automatically checks to see if you are overwriting a file or not and acts accordingly
class SaveQDialog(Screen):
    #Start the path for the file explorer in the given folder.
    path = os.path.expanduser(startingFileFolder)
    #The save function takes a path and filename and saves the current question set at that path.
    def save(self, path, filename):
        global currentQuestionPool, currentSetName
        if filename != None and '.q' in filename[-2:]:#If the filename is not empty and ends in .q
            #Save the file without an added extension (as it already has one)
            with open(os.path.join(path, filename), 'wb') as f:
                pickle.dump(currentQuestionPool, f)
                currentSetName = str(f.name) #Set the currentsetname to be equal to the name of the file selected
        else: #Otherwise, just save the file with the extension added
            with open(os.path.join(path, filename + '.q'), 'wb') as f:
                pickle.dump(currentQuestionPool, f)
                currentSetName = str(f) #Set the currentsetname to be equal to the name of the file selected
        
#The scene that contains options to load and save question sets, as well as the current set name.
#Contains a function that runs on enterance to scene that sets the label involved to the current set name
#Also contains the functions necessary to open a popup with a generated report containing all current questions
class LoadQuestions(Screen):
    #This function is run upon the scene opening
    def on_pre_enter(self):
        self.ids.currentQSet.text = 'Current Set: ' + currentSetName #Set the label on the screen to the current set name
    #This is run when the button to generate a report is pressed.
    #It opens a popup displaying a Text input showing all current questions
    def qReport(self):
        qReportPop = Popup(title='Question Report', content=TextInput(text=self.generateReport()), size_hint=(.8, .6))
        qReportPop.open()
    
    #This generates the text that goes into qReport's report
    def generateReport(self):
        output = ''
        #For every question, add them to the output and add a new line between the data.
        for each in currentQuestionPool:
            output += "ID:" + str(each.id) + " | Elo Score: " + str(int(each.elo)) + " | Question: " + each.question + " | Correct Answer: " + each.corAns + " | Incorrect Answers: " + str(each.possAns[0]) + " | " + str(each.possAns[1]) + " | " + str(each.possAns[2]) +"\n"
        return output

#This is the screen used to save and load user objects. You can also update the username from this screen
class LoadUser(Screen):
    #On this screen's enterance, update the username label and the elo label to display current information
    def on_pre_enter(self):
        self.ids.userName.text = currentUser.name
        self.ids.eloLevel.text = 'Current Elo: ' + str(int(currentUser.elo))
    #If the button to update the username is clicked, update the relevant text.
    def updateUserName(self, name):
        global currentUser
        currentUser.name = name
        self.ids.userName.text = name


#This is the screen used to add questions to the current set. 
class AddQuestions(Screen):
    #This function takes info from the various text input fields and uses them to construct and append a new question object. 
    #It then updates the text fields back to the default info
    def addQuestion(self):
        currentQuestionPool.append(Question(newId(), self.ids.question.text, [self.ids.wrongOne.text, self.ids.wrongTwo.text, self.ids.wrongThree.text], self.ids.correctAnswer.text, getEloFromRating(int(self.ids.slider.value))))
        self.ids.question.text = ''
        self.ids.wrongOne.text = ''
        self.ids.wrongTwo.text = ''
        self.ids.wrongThree.text = ''
        self.ids.correctAnswer.text = ''
        self.ids.slider.value = 3
        

#This is the screen which handles the actual 'Question' and 'answer' cycles
#Contains 6 functions:
#on_pre_enter, which is called when the study screen is entered. It then calls newAnswers
#newAnswers finds a question based on the matchmaking function. It assigns buttons to answers as well
#pickAnswer is called when an answer button is clicked, and with the help of checkCor, determines if the answer is correct
#It then opens an appropriate popup depending on if the answer is correct and changes the elo of the question and the user via the eloChange function
#noQPopup is called when matchmaking shows no compatible questions, jetting the user back to the menu page
#Closed popup is called when the popups are closed, which calls newAnswers again.

class Study(Screen):

    def on_pre_enter(self):
        self.newAnswers()
    #When new answers is called, a new question is found, its answers assigned to a random button each,  
    def newAnswers(self):
        global cQI
        cQI = matchMaking(currentUser) #Get the question
        if cQI == "None":
            noQPopup = Popup(title='No questions', content=Label(text='No Questions Found'), size_hint=(None, None), size=(400, 150))
            noQPopup.bind(on_dismiss=self.noQPopup)
            noQPopup.open()
        else:
            self.ids.currentQ.text = currentQuestionPool[cQI].question
            #Add the answers of the question to a list
            xList = [currentQuestionPool[cQI].possAns[0], currentQuestionPool[cQI].possAns[1], currentQuestionPool[cQI].possAns[2], currentQuestionPool[cQI].corAns]
            #Randomly choose an item from the list and make it the text of a question. Repeat for each
            x = r.choice(xList)
            self.ids.answerBOne.text = x
            xList.remove(x)
            x = r.choice(xList)
            self.ids.answerBTwo.text = x
            xList.remove(x)
            x = r.choice(xList)
            self.ids.answerBThree.text = x
            xList.remove(x)
            x = r.choice(xList)
            self.ids.answerBFour.text = x
            xList.clear()
    #Called when the answered button is picked, and with the help of checkCor, determines if the answer is correct,
    #It then opens an appropriate popup depending on if the answer is correct and changes the elo of the question and the user via the eloChange function
    def pickAnswer(self, picked):
        x = False
        if picked == 1:
            x = self.checkCor(self.ids.answerBOne.text)
        elif picked == 2:
            x = self.checkCor(self.ids.answerBTwo.text)
        elif picked == 3:
            x = self.checkCor(self.ids.answerBThree.text)
        elif picked == 4:
            x = self.checkCor(self.ids.answerBFour.text)
        
        if x:
            eloChange(currentUser, currentQuestionPool[cQI])
            correctPopup = Popup(title='Correct!', content=Label(text='That was Correct!'), size_hint=(None, None), size=(400, 150))
            correctPopup.bind(on_dismiss=self.closedPopup)
            correctPopup.open()
        else:
            eloChange(currentQuestionPool[cQI], currentUser)
            incorrectPopup = Popup(title='Incorrect', content=Label(text='Sorry, the correct answer was: ' + currentQuestionPool[cQI].corAns, markup=True), size_hint=(None, None), size=(400, 150))
            incorrectPopup.bind(on_dismiss=self.closedPopup)
            incorrectPopup.open()
    #noQPopup is called when matchmaking shows no compatible questions, jetting the user back to the menu page
    def noQPopup(self, arg):
        self.manager.current = 'menu'
        return False
    #Closed popup is called when the popups are closed, which calls newAnswers again.
    def closedPopup(self, arg):

        if len(currentUser.previousQuestions) >= questionPoolMem:
            currentUser.previousQuestions.pop(0)
        currentUser.previousQuestions.append(currentQuestionPool[cQI].id)
        self.newAnswers()

        return False
    #Check cor specifically returns true or false depending on if the answer matches the corAns variable of the Question class object
    def checkCor(self, answer):
        return answer == currentQuestionPool[cQI].corAns


#This screen only holds buttons to get to the other screens, as well as a button that quits the program.
class MainMenu(Screen):
    pass

#This is the primary App tree, which holds the screen manager and all the screen widgets
#build is called when the class is built originally. 
class MVPApp(App):
    def build(self):
        #The screenmanager is what controls the different 'screens' of the application
        sm = ScreenManager()
        #Add the screens to the screen manager
        sm.add_widget(MainMenu(name='menu'))
        sm.add_widget(LoadQuestions(name='loadQ'))
        sm.add_widget(LoadUser(name='loadU'))
        sm.add_widget(AddQuestions(name='addQ'))
        sm.add_widget(Study(name='study'))
        sm.add_widget(LoadQDialog(name='LoadQDialog'))
        sm.add_widget(SaveQDialog(name='SaveQDialog'))
        sm.add_widget(LoadUDialog(name='LoadUDialog'))
        sm.add_widget(SaveUDialog(name='SaveUDialog'))
        return sm

#Run the app
MVPApp().run()