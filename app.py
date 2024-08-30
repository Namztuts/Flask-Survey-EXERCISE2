from flask import Flask, request, render_template, redirect, flash, session, make_response
from flask_debugtoolbar import DebugToolbarExtension
from surveys import satisfaction_survey as survey1 #renaming the satisfaction survey variable from surveys.py
from surveys import personality_quiz as survey2 #renaming the personalityquiz variable from surveys.py
from surveys import surveys


app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecret'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)


RESPONSES_KEY = 'responses'
CURRENT_SURVEY_KEY = 'current_survey'


@app.route('/')
def landing():
    '''Home page for survey start'''    
    return render_template('survey_select.html', surveys=surveys)

@app.route('/', methods=['POST']) 
def survey_select():
    survey_label = request.form['survey_label'] #label is coming from form selection
    
    if request.cookies.get(f"completed_{survey_label}"):
        return render_template("dupe.html")
    
    survey = surveys[survey_label]
    session[CURRENT_SURVEY_KEY] = survey_label #adding the survey to the session for survey_key
    return render_template('landing.html', survey=survey)

@app.route('/start', methods=['POST']) #clearing the session
def start_survey(): #starting the survey and creating a list for the responses/clearing if already there
    '''Start survey with clearing the responses'''
    session[RESPONSES_KEY] = []    
    return redirect('/questions/0') #after clearing the session, going to questions route | session{'responses'=[]}


@app.route('/questions/<int:num>') 
def question_handler(num): #make sure to pass the above <num> here as well
    '''Handles the current/next question'''
    
    current_responses = session.get(RESPONSES_KEY) #getting the current responses
    
    survey_label = session[CURRENT_SURVEY_KEY] #grabbing the survey_key from the above in '/' from the form selection
    current_survey = surveys[survey_label] #grabbing the actual survey now from the global surveys dictionary | so now we have a singular survey to work with
    
    question = current_survey.questions[num] #getting the question based on the route num
    
    #ERROR HANDLING
    if (current_responses is None): #trying to access questions before start of survey
        return redirect("/")
    
    if (len(current_responses) == len(current_survey.questions)): #all the questions have been answered
        return redirect("/end")
    
    if (len(current_responses) != num): #trying to access questions out of order
        flash(f'Invalid question id: {num}. Please answer current question before moving on.')
        return redirect(f"/questions/{len(current_responses)}")
    
    #getting the length of both questions and responses to change the button
    q = len(current_survey.questions)-1
    r = len(current_responses)
    
    return render_template('questions.html', question=question, num=num, q=q, r=r, c=current_responses)


@app.route('/answer', methods=['POST']) #questions.html form sends here | POST request
def answer_handler():
    '''Save the responses and go to next question'''
    survey_label = session[CURRENT_SURVEY_KEY]
    current_survey = surveys[survey_label]
    current_responses = session[RESPONSES_KEY]
    
    if 'answer' in request.form: #if there is an answer, proceed | else, redirect to current page
        choice = request.form['answer'] #whatever the previous answer was
        text = request.form.get("text", "")
        
        current_responses.append({"choice": choice, "text": text}) #adding the answer to the current responses
        session[RESPONSES_KEY] = current_responses
        
        if len(current_responses) == len(current_survey.questions):
            return redirect('/end')
        else:
            return redirect(f"/questions/{len(current_responses)}")
        
    else:
        flash(f'Please answer current question before moving on to next question')
        return redirect(f"/questions/{len(current_responses)}")
    
    
@app.route('/end')
def end():
    '''Presents the end of the survey'''
    
    survey_label = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_label]
    responses = session[RESPONSES_KEY]
    
    html = render_template("end.html", survey=survey, responses=responses)

    # Set cookie noting this survey is done so they can't re-do it
    response = make_response(html) #import make_response from flask
    response.set_cookie(f"completed_{survey_label}", "yes", max_age=60)
    
    return response
