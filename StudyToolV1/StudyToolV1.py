#Minimum Viable Product:

import pickle #Pickle is a built in python lib that handles our file saving and loading
import math

#Kivy is a GUI library
from kivy.app import App #Kivy.app is the root for the applications gui
from kivy.lang import Builder #Builder lets the program load an external .kv file for use by kivy, which is a simpler way to code kivy gui widgets
from kivy.uix.screenmanager import ScreenManager, Screen, CardTransition #The screen manager helps our program go from one screen to another
from kivy.uix.textinput import TextInput #Text input is what it says: It is a widget which handles text being inputed in the GUI
from kivy.uix.popup import Popup #kivy.popup handles any popup windows we need (Specifically used for the study screen and the report generator)
from kivy.uix.label import Label #A label is a simple text box. This isn't used much on this side of the application, just for the hard coded popup boxes
import os #Used for handling paths for files
import random as r #A built in lib for generating random numbers. Used once for choosing where to place answers in the Study screen
import csv #a build in lib for handling comma seperated values
from kivy_garden.graph import Graph, SmoothLinePlot, BarPlot

defaultElo = 1000 #The default elo score
kValue = 50 #The "Pot" of points the players are playing for. 
currentQuestionPool = [] #The pool of questions currently loaded for the user
currentSetName = '' #The name of the current pool of questions
cQI = 0 #The current question's index number. Defaults to 0
questionPoolMem = 5 #The number of questions that can be kept in previous questions
eloMem = 100 #The number of Elo results kept
kvFileName = 'kivyMarkupV1.kv' #The name of the .kv file to be loaded
startingFileFolder = '~/Documents'
userFileName = 'TestUsers'
stemPlotMem = []

class Question:
    def __init__(self, id, question, possAns, corAns, elo):
        self.id = id #A unique ID provided at time of question creation
        self.question = question #A string of the question to be posed
        self.possAns = possAns #A list of possible answers as strings
        self.corAns = corAns #The correct answer, as a string
        self.elo = elo #A score to help determine a questions difficulty based on the elo ranking system
        self.eloHist = [elo] #A list including previous elo amounts for the question

class User:
    def __init__(self, id, name):
        self.id = id #A unique ID given at creation
        self.name = name #A non unique name of the user
        self.elo = defaultElo #A score to help determine the current questions the user will go against
        self.eloHist = [defaultElo] #A list including previous elo amounts. 
        self.previousQuestions = [] #A list of ids of the previous 20 questions answered
        


currentUser = User(0, 'N/a') #Defines a blank current user

#Given the path to a CSV file with questions inputed, add to currentQuestionPool
def importQuestionSet(fileName):
    with open(fileName, newline='') as f:
        newRead = csv.reader(f)
        newList = list(newRead)
        newList.pop(0)
    for each in newList:
        currentQuestionPool.append(Question(newId(), str(each[1]), [str(each[3]), str(each[4]), str(each[5])], str(each[2]), getEloFromRating(each[6])))
    f.close()

#Given the path to a file with the user's, and the filename of a CSV with the test data inputed, update the elo of the users
def importTestData(userLoc, fileName):
    with open(fileName, newline='') as f:
        newRead = csv.reader(f)
        newList = list(newRead)
        newList.pop(0)
    for each in newList:
        if each[2] == '1': #If the question was correct:
            with open(os.path.join(userLoc, each[0]), 'rb') as f:
                user = pickle.load(f)
                f.close()
            eloChange(user, Question(0, '', '', '', getEloFromRating(each[1])))
            with open(os.path.join(userLoc, each[0]), 'wb') as f:
                pickle.dump(user, f)
                f.close()
        elif each[2] == '0':
            with open(os.path.join(userLoc, each[0]), 'rb') as f:
                user = pickle.load(f)
                f.close()
            eloChange(Question(0, '', '', '', getEloFromRating(each[1])), user)
            with open(os.path.join(userLoc, each[0]), 'wb') as f:
                pickle.dump(user, f)
                f.close()


#Calculates the probability of a user succeding per the Elo ranking system.
def calcProb(rA, rB): 
    return 1.0 / (1.0 + math.pow(10, ((rB - rA)/400)))

#Given a winner and a loser of a 'match', change the elo scores appropriately
def eloChange(winner, loser): 
    pWin = calcProb(loser.elo, winner.elo) #Calculate the probability of the winner having won
    pLose = calcProb(winner.elo, loser.elo) #Calculate the loser's chances
    #Elo's equation: R(a) = a + K * (S - P), R(a) is the resulting score, a is the score, K is the "Pot", S is some number between 0 and 1 for how well the 'player' did, and P is the probability of winning
    winner.elo = winner.elo + kValue * (1 - pWin) #Change the winners score equal to the elo equation given
    winner.eloHist.append(winner.elo) #adds the latest elo to the history
    loser.elo = loser.elo + kValue * (0 - pLose) #Change the losers score equal to the given elo equation
    loser.eloHist.append(loser.elo) #Adds the latest elo to the history
    if len(winner.eloHist) > eloMem: #Gets rid of oldest in mem if there are more than the elo mem amount
        winner.eloHist.pop[0]
    if len(loser.eloHist) > eloMem: #Gets rid of oldest in mem if there are more than the elo mem amount
        loser.eloHist.pop[0]

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

class ImportTestDialog(Screen):
    path = os.path.expanduser(startingFileFolder)

    def importCsv(self, selection, pathGiven):
        importTestData(pathGiven, selection)

class ImportQuestionsDialog(Screen):
    path = os.path.expanduser(startingFileFolder)
    def importCsv(self, selection):
        importQuestionSet(selection)

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
    
    
    def clearQuestions(self):
        global currentQuestionPool
        currentQuestionPool.clear()
    

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

class ReportPage(Screen):
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

#This screen displays a bar graph that includes all the questions based on their Score and ID
class BarGraphScorePage(Screen):
    def on_pre_enter(self, *args):
        #Create a graph, aka the box around the bar plot.
        self.graph1 = Graph(xlabel='Question IDs', ylabel='Score', y_grid_label=True, x_grid_label=True, 
                            y_grid=True, xmin=0, xmax=int(len(currentQuestionPool)) + 1, 
                            ymin=0, ymax=2000, y_ticks_major=200, y_ticks_minor=50, x_ticks_major=1)
        #Create the barplot, set its color to red, and set its bar width to 50 pixels
        plot = BarPlot(color=[1,0,0,1])
        plot.bar_width = 50
        #Generate the points (See generatePoints function)
        plot.points = self.generatePoints()
        #Add the plot to the graph
        self.graph1.add_plot(plot)
        #Add the graph to the screen as a widget under the boxlayout labeled 'graph'
        self.ids.graph.add_widget(self.graph1)
        return super().on_pre_enter(*args)
    #When the screen is left, delete the graph widget to prevent stacking
    def on_leave(self, *args):
        self.ids.graph.remove_widget(self.graph1)
        return super().on_leave(*args)
    #Generate the individual 'points' on the graph. These are tuples with an x and y coordinate that the bar will be made at
    def generatePoints(self):
        output = []
        x = .6 #Start the x axis at about half a point (For aethstetic purposes)
        for each in currentQuestionPool:
            output.append([x,each.elo]) #For each in the current question set, add its elo as the y axis for a point
            x += 1
        return output

#This screen displays a line graph of the current users history of elo scores, as it has changed over time.
class LineGraphScorePage(Screen):
    def on_pre_enter(self, *args):
        #First, label the graph as the users name + score over time
        self.ids.lineGraphLabel.text = str(currentUser.name) + "'s Score Over Time"
        #Create the graph object, which is where the actual plot (with the data) will go. provides context to data
        self.graph1 = Graph(xlabel='Questions ago', ylabel='Score', y_grid_label=True, x_grid_label=True, 
        x_grid=True, xmin=int(-1 * len(currentUser.eloHist)), xmax=-1, ymin=int(min(currentUser.eloHist))-50, ymax=int(max(currentUser.eloHist))+50, y_ticks_major=100, y_ticks_minor=50, x_ticks_major=1)
        #Create the plot as a smooth line plot (Looks nicer than standard line plot)
        #Make the plot yellow
        #Then, add the points per generateUserScore. The points are pairs of x,y coordinates in a list
        plot = SmoothLinePlot(color=[1,1,0,1])
        plot.points = self.generateUserScore()
        #add the plot to the graph
        self.graph1.add_plot(plot)
        #Add the graph to the screen as a child of the graph boxlayout
        self.ids.graph.add_widget(self.graph1)
        return super().on_pre_enter(*args)
    def on_leave(self, *args):
        #When the screen is left, delete the graph widget to prevent stacking
        self.ids.graph.remove_widget(self.graph1)
        return super().on_leave(*args)
    #Sends back a list of the elo history as points on the graph
    def generateUserScore(self):
        output = []
        x = -len(currentUser.eloHist)
        for each in currentUser.eloHist:
            output.append([x, each])
            x += 1
        return output

#On this screen, the users to be used in the stem plot are selected using a filechooser
class StemPlotSelectPage(Screen):
    path = os.path.expanduser(startingFileFolder)

    def selectUsers(self, users, path): #When the select button is clicked, run this
        global stemPlotMem
        for each in users: #For each user selected, load its elo score into the stemplotmem
            with open(os.path.join(path, each), 'rb') as f:
                stemPlotMem.append(pickle.load(f).elo)
                f.close()
        
#this displays the selected users elo scores as a stem plot
class StemPlotScorePage(Screen):
    labelArray = [] #This will hold the labels created for the stem plot
    def on_pre_enter(self, *args):
        #this will hold the sorted stemPlotMem data
        stemPlotArray = [[],[],[],[],[],[],[],[],[],[],[],[],[]] 
        #This for statement sorts the stemplotmem into appropriate lists
        for each in stemPlotMem:
            if each < 500:
                stemPlotArray[0].append(each)
            elif each >= 500 and each < 600:
                stemPlotArray[1].append(each)
            elif each >= 600 and each < 700:
                stemPlotArray[2].append(each)
            elif each >= 700 and each < 800:
                stemPlotArray[3].append(each)
            elif each >= 800 and each < 900:
                stemPlotArray[4].append(each)
            elif each >= 900 and each < 1000:
                stemPlotArray[5].append(each)
            elif each >= 1000 and each < 1100:
                stemPlotArray[6].append(each)
            elif each >= 1100 and each < 1200:
                stemPlotArray[7].append(each)
            elif each >= 1200 and each < 1300:
                stemPlotArray[8].append(each)
            elif each >= 1300 and each < 1400:
                stemPlotArray[9].append(each)
            elif each >= 1400 and each < 1500:
                stemPlotArray[10].append(each)
            elif each >= 1500 and each < 1600:
                stemPlotArray[11].append(each)
            else:
                stemPlotArray[12].append(each)
        #Create a label for each non empty list in stemPlotArray. see generateLabel() for details
        for each in stemPlotArray:
            if len(each):
                self.labelArray.append(Label(text=self.generateLabel(each), font_size='30sp'))
        #Then add the widgets to the screen
        for each in self.labelArray:
            self.ids.stemPlot.add_widget(each)
        #Clear the stemPlotArray for cleaning purposes
        stemPlotArray.clear()
        return super().on_pre_enter(*args)
    def on_leave(self, *args):
        #When the screen is exited, clear the widgets and memories to prevent overcrowding or doubling
        global stemPlotMem
        self.ids.stemPlot.clear_widgets()
        self.labelArray.clear()
        stemPlotMem.clear()
        return super().on_leave(*args)
    #sort the given list, give it a value starter, then add the last 2 digits of the lists items to the string. return as string.
    def generateLabel(self, list):
        output = ''
        if list[0] < 500:
            output = '>500   ||  '
        elif list[0] >= 500 and list[0] < 600:
            output = '500   ||  '
        elif list[0] >= 600 and list[0] < 700:
            output = '600   ||  '
        elif list[0] >= 700 and list[0] < 800:
            output = '700   ||  '
        elif list[0] >= 800 and list[0] < 900:
            output = '800   ||  '
        elif list[0] >= 900 and list[0] < 1000:
            output = '900   ||  '
        elif list[0] >= 1000 and list[0] < 1100:
            output = '1000   ||  '
        elif list[0] >= 1100 and list[0] < 1200:
            output = '1100   ||  '
        elif list[0] >= 1200 and list[0] < 1300:
            output = '1200   ||  '
        elif list[0] >= 1300 and list[0] < 1400:
            output = '1300   ||  '
        elif list[0] >= 1400 and list[0] < 1500:
            output = '1400   ||  '
        elif list[0] >= 1500 and list[0] < 1600:
            output = '1500   ||  '
        else:
            output = '<1599   ||  '
        for each in list:
            output += str(each)[-2:] + ", "
        return output



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
        sm.add_widget(ImportTestDialog(name='ImportTestDialog'))
        sm.add_widget(ImportQuestionsDialog(name='ImportQuestionsDialog'))
        sm.add_widget(ReportPage(name='reports'))
        sm.add_widget(LineGraphScorePage(name='lineGraph'))
        sm.add_widget(BarGraphScorePage(name='barGraph'))
        sm.add_widget(StemPlotSelectPage(name='stemSelect'))
        sm.add_widget(StemPlotScorePage(name='stemScore'))
        return sm

#Run the app
MVPApp().run()