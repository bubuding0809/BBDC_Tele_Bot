import logging
from telegram import Animation, CallbackQuery, ChatAction, InlineKeyboardMarkup, ReplyMarkup
from telegram.ext import (
    Updater, 
    CommandHandler, 
    CallbackContext, 
    Filters, 
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler
)
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove, 
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Globals
USERNAME, PASSWORD, RANGE, DATE, SLOT = range(5)
credentials = {
    'username' : '060C16091999',
    'password' : '030918'
}
param = {
    'range' : 5,
    'date' : '25/04/2022',
    'slot' : 0
}
kill_status = False
bot_status = False
tryCounter = 1

# Selenium chrome settings
options = Options()
options.headless = True
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")

#********************************Telegram update handler functions implementations**********************************#
def start(update: Update, context: CallbackContext):
    logger.info("/start used")
    #reply_keyboard = [['/help', '/setup', '/run', '/kill', '/status']]
    inline_keyboard = [
        [
            InlineKeyboardButton("help", callback_data='help'),
            InlineKeyboardButton("setup", callback_data='setup_menu')
        ],
        [
            InlineKeyboardButton("run", callback_data='run'),
            InlineKeyboardButton("kill",callback_data='kill')
        ]
    ]
    message = '''Welcome to the BBDC driving lesson booking bot.\n\nYou can use the following commands to control me:
    
/help - list of commands you can execute
/setup - enter BBDC account login infomation, and search parameters
/run - run web-automation bot once account setup is done
/kill - kill web-automation bot running in the background
/status - Check on bot statues
'''
    
    update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )
    
    logger.info("Started")

def setup(update: Update, context: CallbackContext) -> int:
    user = update.effective_chat
    inline_keyboard = [
            [InlineKeyboardButton("Full setup", callback_data="full_setup")],
            [
                InlineKeyboardButton("username", callback_data="username"),
                InlineKeyboardButton("password", callback_data="password")
            ],
            [
                InlineKeyboardButton("range", callback_data="range"),
                InlineKeyboardButton("date", callback_data="date"),
                InlineKeyboardButton("slot", callback_data="slot")
            ],
            [InlineKeyboardButton("Run bot when ready.", callback_data="run")]
        ]
    
    try:
        query = update.callback_query
        query.answer()
    except:
        context.bot.send_message(chat_id=user.id, text="Choose between the list of parameters or full setup", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    else:
        query.edit_message_text(text="Choose between the list of parameters or a full setup.", reply_markup=InlineKeyboardMarkup(inline_keyboard))
        logger.info("/setup used")
    
    return ConversationHandler.END
        
def full_setup(update:Update, context: CallbackContext) -> int:
    user = update.effective_chat
    query = update.callback_query
    query.answer(text = "Proceeding with full account setup", show_alert=True)
    
    inline_keyboard = [
        [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
    ]
    query.edit_message_text(text="Enter your BBDC account username:", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    
    return USERNAME

def username(update: Update, context: CallbackContext) -> int:
    global credentials
    user = update.effective_chat
    logger.info(f"BBDC Username of {user.first_name}: {update.message.text} entered.")
    credentials["username"] = update.message.text
    inline_keyboard = [
        [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
    ]
    context.bot.send_message(chat_id=user.id, text="Please enter your BBDC password without anyone looking", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    
    return PASSWORD

def password(update: Update, context: CallbackContext) -> int:
    global credentials
    user = update.message.from_user
    logger.info(f"BBDC password of {user.first_name}: {update.message.text} entered.")
    credentials["password"] = update.message.text
    inline_keyboard = [
        [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
    ]
    context.bot.send_message(chat_id=user.id, text="Enter range of slots to poll for (eg: 3)", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    
    return RANGE
    
def search_range(update: Update, context: CallbackContext) -> int:
    global param
    user = update.effective_chat
    logger.info(f"search range of {user.first_name}: {update.message.text} entered.")
    
    try:
        param["range"] = int(update.message.text)
    except ValueError:
        update.message.reply_text('Please re-enter a valid search range type: (int)')
        return RANGE

    inline_keyboard = [
        [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
    ]
    context.bot.send_message(chat_id=user.id, text="Please enter date of slot to be booked in DD/MM/YYYY, if not booking, just enter nil", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    
    return DATE

def date(update: Update, context: CallbackContext) -> int:
    global param
    user = update.effective_chat
    logger.info(f"Date of desired slot of {user.first_name}: {update.message.text} entered.")
    param["date"] = update.message.text
    inline_keyboard = [
        [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
    ]
    context.bot.send_message(chat_id=user.id, text="Please enter slot number to be booked. Available slots are 1 to 7 (eg: 5)", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    
    return SLOT

def slot(update: Update, context: CallbackContext) -> int:
    global param
    user = update.effective_chat
    logger.info(f"desired slot of {user.first_name}: {update.message.text} entered.")
    
    try:
        param["slot"] = int(update.message.text)
    except ValueError:
        update.message.reply_text('Please re-enter a valid slot type: (int) between 1 to 7')
        return SLOT
    
    inline_keyboard = [
        [InlineKeyboardButton(text="Run bot", callback_data="run")]
    ]
    context.bot.send_message(chat_id=user.id, text="Thank your for submitting all relevant information, you may run the bot now", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.effective_chat
    logger.info("User %s canceled the setup process.", user.first_name)
    inline_keyboard = [
            [InlineKeyboardButton("Run bot", callback_data="run")]
        ]
    context.bot.send_message(chat_id=user.id, text="If you are done with the setup please use /run to run bot", reply_markup=InlineKeyboardMarkup(inline_keyboard))

    return ConversationHandler.END

def dev_log(update: Update, context: CallbackContext):
    logger.info(f"Username: {credentials['username']}")
    logger.info(f"Password: {credentials['password']}")
    logger.info(f"range: {param['range']}")
    logger.info(f"date: {param['date']}")
    logger.info(f"slot: {param['slot']}")
    
    
    update.message.reply_text(f'''This are your entered credientials:
        username: {credentials["username"]}
        password: {credentials["password"]}
        Search range: {param["range"]}
        Search date: {param["date"]}
        Search slot: {param["slot"]}
    ''')

def run_bot(update: Update, context: CallbackContext):
    user = update.effective_chat
    global kill_status, bot_status, tryCounter
    kill_status = False
    bot_status = True
    
    try:
        query = update.callback_query
        query.answer()
    except:
        pass
    
    inline_keyboard = [
        [
            InlineKeyboardButton("Kill bot", callback_data="kill"),
            InlineKeyboardButton("Check status", callback_data="status")
        ]
    ]
    try:    
        query.edit_message_text(
            text="Bot running, option below to stop bot", 
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )
    except:
        pass
 
    #Begin login proceess
    try:
        id = credentials["username"]
        pw = credentials["password"]
        range = param["range"]
        date = param["date"]
        slot = param["slot"]
    except KeyError:
        logger.exception("User did not enter all required fields")
        context.bot.send_message(chat_id=user.id, text=f"{user.first_name} did not enter all required fields")
        #update.message.reply_text(f"{user.first_name} did not enter all required fields")
    else:   
        #Let user know bot is running
        logger.info("bot started")
        context.bot.send_message(chat_id=user.id, text="Bot is running, please hold still")
        #update.message.reply_text("Bot is running, please hold still")
        context.bot.send_chat_action(chat_id=user.id, action=ChatAction.TYPING, timeout=30)
        
        while True:
            #Open automated browser and login
            browser = login(id, pw, range, date, slot, update, context)
            
            #Catch login error message and let user know stop bot
            if type(browser) == str:
                logger.info(f"An error occured: {browser}")
                
                if "password" in browser:
                    context.bot.send_animation(chat_id=user.id, animation="https://i.gifer.com/y7.gif", caption="Incorrect password entered")
                else:
                    context.bot.send_animation(chat_id=user.id, animation="https://i.gifer.com/y7.gif", caption="Invalid username entered")

                context.bot.send_message(chat_id=user.id, text="Please make sure your login information is correct, use /setup to re-enter information")
                logger.info("bot stopped")
                bot_status = False
                
                return
            
            #Catch logging error due to bad BBDC server
            elif browser == None:
                logger.info("bot stopped")
                inline_keyboard = [
                    [
                        InlineKeyboardButton("Return to setup", callback_data="setup_menu"),
                        InlineKeyboardButton("Run bot again", callback_data="run")
                    ]
                ]
                context.bot.send_message(chat_id=user.id, text="Bot killed", reply_markup=InlineKeyboardMarkup(inline_keyboard))
                bot_status = False
                
                return
            
            #login successful, let user know
            context.bot.send_message(chat_id=user.id, text="Login successful, proceeding with checking available slots")
            
            #If an instance of the browser is returned, proceed with selecting 3A booking page
            non_fixed_instructor_page(browser)
            
            #Select search page options
            selection_menu(browser)
            
            #Reset try-counter to 1 prior to initiating slot polling
            tryCounter = 1
            comp_data = []
            reload_flag = True
            while reload_flag == True:
                slot_flag, data = poll_slots(range, date, slot + 1, browser)
                
                if slot_flag == True:
                    
                    break
                
                elif slot_flag == None:
                    comp_data.clear()
                    
                    break
                
                if kill_status is True:
                    logger.info(f"kill status: {kill_status} ")
                    browser.close()
                    logger.info("Bot killed")
                    inline_keyboard = [
                        [
                            InlineKeyboardButton("Return to setup", callback_data="setup_menu"),
                            InlineKeyboardButton("Run bot again", callback_data="run")
                        ]
                    ]
                    context.bot.send_message(chat_id=user.id, text="Bot killed", reply_markup=InlineKeyboardMarkup(inline_keyboard))
                
                    #reset status flags to default
                    bot_status = False
                    kill_status = False
                    
                    return
                
                if comp_data != data:
                    slot_info = "\n".join(data)
                    inline_keyboard = [
                        [
                            InlineKeyboardButton("Kill bot", callback_data="kill"),
                            InlineKeyboardButton("Check status", callback_data="status")
                        ]
                    ]
                    context.bot.send_message(chat_id=user.id, text=slot_info, reply_markup=InlineKeyboardMarkup(inline_keyboard))
                
                #store current data into reference variable
                comp_data = data
                
                reload_flag = reload_slots(browser, 5)

            if reload_flag == False:
                browser.close()
                continue        
            #If slot found, book slot
            elif not comp_data:
                browser.close()
                continue
            else:
                book_slot(browser)
                logger.info(f"{date} {slot} Slot booked")
                browser.close()
                bot_status = False
        
def kill(update: Update, context: CallbackContext):
    global kill_status, bot_status
    user = update.effective_chat
    
    #Send kill signal to bot by setting kill_status to True, if bot is not running let user know
    context.bot.send_message(chat_id=user.id, text="Sending signal to kill bot")
    kill_status = True
    context.bot.send_chat_action(chat_id=user.id, action=ChatAction.TYPING, timeout=1)
    
    if bot_status == False:
        context.bot.send_message(chat_id=user.id, text="Do not try to kill a dead bot")
    
def send_status(update: Update, context: CallbackContext):
    user = update.effective_chat
    message = ""
    
    if bot_status == True and kill_status == True:
        message = "STATUS: Bot is currently running but an assassin has been sent to kill it"
    elif bot_status == True and kill_status == False:
        message = "STATUS: Bot is well and alive with no one trying to kill it"
    elif bot_status == False and kill_status == True:
        message = "STATUS: Bot is dead but someone still is trying to kill it"
    else:
        message = "STATUS: Bot is dead, feel free to revive him with /run"
    
    context.bot.send_message(chat_id=user.id, text=message)

def indv_id(update: Update, context: CallbackContext):
    user = update.effective_chat
    query = update.callback_query
    query.answer()
    
    logger.info("User chose to edit username")
    inline_keyboard = [
        [
            InlineKeyboardButton("back", callback_data="back")
        ]
    ]
    query.edit_message_text("Enter BBDC account username:", reply_markup=InlineKeyboardMarkup(inline_keyboard))

    return USERNAME

def id(update: Update, context: CallbackContext) -> int:
    global credentials
    user = update.effective_chat
    logger.info(f"BBDC Username of {user.first_name}: [{update.message.text}] entered.")
    credentials["username"] = update.message.text
    
    inline_keyboard = [
            [InlineKeyboardButton("Full setup", callback_data="full_setup")],
            [
                InlineKeyboardButton("username", callback_data="username"),
                InlineKeyboardButton("password", callback_data="password")
            ],
            [
                InlineKeyboardButton("range", callback_data="range"),
                InlineKeyboardButton("date", callback_data="date"),
                InlineKeyboardButton("slot", callback_data="slot")
            ],
            [InlineKeyboardButton("Run bot when ready.", callback_data="run")]
        ]
    
    context.bot.send_message(chat_id=user.id, text="Username successfully entered", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    
    return ConversationHandler.END

def indv_pw(update: Update, context: CallbackContext):
    user = update.effective_chat
    query = update.callback_query
    query.answer()
    
    logger.info("User chose to edit password")
    inline_keyboard = [
        [
            InlineKeyboardButton("back", callback_data="back")
        ]
    ]
    query.edit_message_text("Enter BBDC account password:", reply_markup=InlineKeyboardMarkup(inline_keyboard))

    return PASSWORD

def pw(update: Update, context: CallbackContext):
    global credentials
    user = update.effective_chat
    logger.info(f"BBDC password of {user.first_name}: [{update.message.text}] entered.")
    credentials["password"] = update.message.text
    
    inline_keyboard = [
            [InlineKeyboardButton("Full setup", callback_data="full_setup")],
            [
                InlineKeyboardButton("username", callback_data="username"),
                InlineKeyboardButton("password", callback_data="password")
            ],
            [
                InlineKeyboardButton("range", callback_data="range"),
                InlineKeyboardButton("date", callback_data="date"),
                InlineKeyboardButton("slot", callback_data="slot")
            ],
            [InlineKeyboardButton("Run bot when ready.", callback_data="run")]
        ]
    
    context.bot.send_message(chat_id=user.id, text="Password successfully entered", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    
    return ConversationHandler.END

def indv_range(update: Update, context: CallbackContext):
    pass

def indv_date(update: Update, context: CallbackContext):
    pass

def indv_slot(update: Update, context: CallbackContext):
    pass

#******************************Selenium Webdriver*****************************#
def login(id, pw, range, date, slot, update, context):
    global options
    user = update.effective_chat
    browser = webdriver.Chrome("DRIVER", options=options)
    logger.info(f"App start\nPolling for up to {range} days, [{date}] slot {slot} to be booked")
    
    while True:
        if kill_status == True:
            browser.close()
            
            return
        
        try:
            browser.get("SITE")
            wait = WebDriverWait(browser, 60)
            wait.until(EC.visibility_of_element_located((By.ID, "members-login-holder")))
            
            # Login 
            idLogin = browser.find_element_by_id('txtNRIC')
            idLogin.send_keys(id)
            idLogin = browser.find_element_by_id('txtPassword')
            idLogin.send_keys(pw)
            loginButton = browser.find_element_by_name('btnLogin')
            loginButton.click()

            #dismiss form submittion warning and proceed into account, does not pop up in headless mode
            if not options.headless:
                proceed = browser.find_element_by_id('proceed-button')
                proceed.click()
        
        #If exception is raised when trying to access site, close browser and try again
        except Exception as e:
            logger.exception("Exception occurred")
            context.bot.send_message(chat_id=user.id, text="Trying to loggin, please be patient")
            #update.message.reply_text("Trying to logging, please be patient")
        
        #Else try to check if there is any alert message regards to login
        else:
            try:
                #wait = WebDriverWait(browser, 3)
                #wait.until(EC.alert_is_present())
                alert_message = browser.switch_to.alert.text
            
            #If there is not alert message, try to switch to leftframe
            except Exception as e:
                logger.info("No alert text exception")
                try:
                    #Switch to leftframe
                    browser.switch_to.default_content()
                    frame = browser.find_element_by_name('leftFrame')
                    browser.switch_to.frame(frame)
                
                #If leftFrame does not exist, close browser and try again
                except Exception as e:
                    logger.exception("Exception occurred")
                    context.bot.send_message(chat_id=user.id, text="Trying to login, please be patient")

                
                #Else if left frame exist, return browser and proceed
                else:
                    return browser  
            
            # If there is alert message, return alert message
            else:
                return alert_message
            
def non_fixed_instructor_page(browser):
    nonFixedInstructor = browser.find_element_by_link_text('Booking without Fixed Instructor')
    nonFixedInstructor.click()

    # Switching back to Main Frame and pressing 'I Agree btn'
    browser.switch_to.default_content()
    wait = WebDriverWait(browser, 300)
    wait.until(EC.frame_to_be_available_and_switch_to_it(browser.find_element_by_name('mainFrame')))
    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "btn"))).click()

def selection_menu(browser):
    # Selection menu
    browser.switch_to.default_content()
    wait = WebDriverWait(browser, 300)
    wait.until(EC.frame_to_be_available_and_switch_to_it(browser.find_element_by_name('mainFrame')))
    wait.until(EC.visibility_of_element_located((By.ID, "checkMonth")))

    # 0 refers to first month, 1 refers to second month, and so on...
    months = browser.find_elements_by_id('checkMonth')
    for i in range(0,5):
        months[i].click()

    # 0 refers to first session, 1 refers to second session, and so on...
    sessions = browser.find_elements_by_id('checkSes')
    sessions[8].click() # all sessions

    # 0 refers to first day, 1 refers to second day, and so on...
    days = browser.find_elements_by_id('checkDay')
    days[7].click() # all days

    # Selecting Search
    search_button = browser.find_element_by_name('btnSearch')
    search_button.click()
    
    try:
        wait = WebDriverWait(browser, 30)
        wait.until(EC.alert_is_present())
    except:
        return
    
    alert_obj = browser.switch_to.alert
    alert_obj.accept()      
        
def poll_slots(rangeUpper, Selectdate, slot, browser):
    global tryCounter
    data = []
    try:
        table = browser.find_element_by_xpath('/html/body/table/tbody/tr/td[2]/form/table[1]/tbody/tr[10]/td/table/tbody')
        rows = table.find_elements_by_tag_name('tr')
    except:
        return None, data
    
    #Poll for available slots based on predefined search range
    for i in range(2,rangeUpper + 2): 
        
        #split date text into list to be processed
        date = rows[i].text.split()
        date.pop()
        cols = rows[i].find_elements_by_tag_name('td')
        for j in range(2, len(cols)):
            if cols[j].find_elements_by_name('slot'):
                logger.info(f"{date}: Slot {j-1} available")
                
                #create string containing available date and slot
                try:
                    #date.pop()
                    temp_str = " ".join(date) + " Slot: *" + str(j-1) + "* available"
                    data.append(temp_str)
                except IndexError:
                    pass
                    
    #Check if predefined date and slot is avaiable, if true return true, else return false        
    for i in range(2,len(rows)): 
        
        #split date text into list to be processed
        date = rows[i].text.split()
        # Check if date matches
        if Selectdate in date:
            #Click on desired slot
            cols = rows[i].find_elements_by_tag_name('td')
            selection = cols[slot].find_elements_by_name('slot')
            
            #Check if desired slot is available, if not return false
            if len(selection) == 0:
                logger.info(f"{Selectdate} Slot: {slot-1} not available. Try: {tryCounter}")
                data.append(f"\nTried booking slot {slot-1} from {Selectdate}, slot is not vacant")
                tryCounter += 1
                return False, data
        
            #if available, return true
            selection[0].click()
            return True, data
    
    # If desired date is not available, print "Date not found" and return false 
    logger.info(f"{Selectdate} Slot {slot-1} not found. Try: {tryCounter}")
    data.append(f"\nTried booking slot {slot-1} from {Selectdate}, date does not have any slot vacant")
    tryCounter += 1
    return False, data

def reload_slots(browser, pollPeriod):
    # Reload slots page after function returns that slot has yet to be found
    browser.back()
    logger.info(f"Poll again in {pollPeriod} seconds")
    time.sleep(pollPeriod)
    
    wait = WebDriverWait(browser, 15)
    wait.until(EC.frame_to_be_available_and_switch_to_it(browser.find_element_by_name('mainFrame')))
    search = browser.find_element_by_name('btnSearch')
    search.click()
    logger.info("Search button clicked")
    
    try:
        wait.until(EC.alert_is_present())
    except:
        logger.exception("alert not found error")
        return False
    else:
        alert_obj = browser.switch_to.alert
        alert_obj.accept()
    return True

def book_slot(browser):
    # Selecting Submit
    browser.find_element_by_name('btnSubmit').click()

    # Selecting confirm
    wait = WebDriverWait(browser, 100)
    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@value='Confirm']")))
    browser.find_element_by_xpath("//input[@value='Confirm']").click()

    # Dismissing alert prompt
    wait.until(EC.alert_is_present())
    alert_obj = browser.switch_to.alert
    alert_obj.accept()
    
# MAIN
def main():
    updater = Updater(token="TOKEN")
    disp = updater.dispatcher

    fullsetup_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(full_setup, pattern='^full_setup$')],
            states={
                USERNAME : [MessageHandler(Filters.text & ~Filters.command, username)],
                PASSWORD : [MessageHandler(Filters.text & ~Filters.command, password)],
                RANGE : [MessageHandler(Filters.text & ~Filters.command, search_range)],
                DATE : [MessageHandler(Filters.text & ~Filters.command, date)],
                SLOT: [MessageHandler(Filters.text & ~Filters.command, slot)]
            },
            fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')],
        )

    indvsetup_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(indv_id, pattern='^username$'),
                CallbackQueryHandler(indv_pw, pattern='^password$'),  
                CallbackQueryHandler(indv_range, pattern='^range$'),  
                CallbackQueryHandler(indv_date, pattern='^date$'),  
                CallbackQueryHandler(indv_slot, pattern='^slot$'),      
            ],
            states={
                USERNAME : [MessageHandler(Filters.text & ~Filters.command, id)],
                PASSWORD : [MessageHandler(Filters.text & ~Filters.command, pw)]
            },
            fallbacks=[CallbackQueryHandler(setup, pattern='^back')]
        )
    
    disp.add_handler(fullsetup_conv_handler)
    disp.add_handler(indvsetup_conv_handler)
    
    disp.add_handler(CommandHandler("start", start))
    disp.add_handler(CommandHandler("help", start))
    disp.add_handler(CommandHandler("setup", setup))
    disp.add_handler(CommandHandler('dev_log', dev_log))
    disp.add_handler(CommandHandler('status', send_status))
    disp.add_handler(CommandHandler('kill', kill, run_async=True))
    disp.add_handler(CommandHandler('run', run_bot, run_async= True))
    disp.add_handler(CallbackQueryHandler(setup, pattern='^setup_menu$'))
    disp.add_handler(CallbackQueryHandler(run_bot, pattern='^run$', run_async= True))
    disp.add_handler(CallbackQueryHandler(kill, pattern='^kill$', run_async=True))
    disp.add_handler(CallbackQueryHandler(send_status, pattern='^status$'))
    
    #Start bot
    updater.start_polling()
    updater.idle()
    
if __name__ == "__main__":
    main()