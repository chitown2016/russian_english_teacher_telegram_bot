from typing import Final
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from dotenv import find_dotenv, load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from enum import Enum
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import datetime as dt
import pytz
import pandas as pd
import random
import os
import json

common_verbs = [
    "be", "have", "do", "say", "go", "can", "get", "would", "make", "know",
    "will", "think", "take", "see", "come", "could", "want", "look", "use", "find",
    "give", "tell", "work", "may", "should", "call", "try", "ask", "need", "feel",
    "become", "leave", "put", "mean", "keep", "let", "begin", "seem", "help", "talk",
    "turn", "start", "might", "show", "hear", "play", "run", "move", "like", "live",
    "believe", "hold", "bring", "happen", "must", "write", "provide", "sit", "stand", "lose",
    "pay", "meet", "include", "continue", "set", "learn", "change", "lead", "understand", "watch",
    "follow", "stop", "create", "speak", "read", "allow", "add", "spend", "grow", "open",
    "walk", "win", "offer", "remember", "love", "consider", "appear", "buy", "wait", "serve",
    "die", "send", "expect", "build", "stay", "fall", "cut", "reach", "kill", "remain"
]

class BotMode(Enum):
    EXAMPLE_SENTENCES = 1
    LANGUAGE_GAME = 2

class TeacherBot:

    def __init__(self):
        self.bot_mode = BotMode.EXAMPLE_SENTENCES
        self.word_frame = pd.read_table('word_list.txt',names=['word'])

    async def example_sentences(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        self.bot_mode = BotMode.EXAMPLE_SENTENCES
        await update.message.reply_text('I will provide 5 example sentences and their russian translations. Please enter a word')

    async def game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        self.bot_mode = BotMode.LANGUAGE_GAME

        test_string = self.generate_test_string()
    
        await update.message.reply_text('Давайте играть и увеличивать ваш счет \n' + test_string)


    def generate_test_string(self) -> str:
        output_parser = JsonOutputParser(pydantic_object=MultipleChoiceQuestion)

        questionType = random.randint(0, 2)

        if questionType == 0:

            system_message_prompt = SystemMessagePromptTemplate.from_template("Human is a native russian who is trying to learn english. \
                                                                                First construct a grammatically correct english sentence using the word: {word1}. \
                                                                                You can use the word as is or transform it as needed in the sentence. \
                                                                                Please be absolutely certain that the sentence is grammatically correct. \
                                                                                Then remove the word {word1} from the sentence to construct a multiple choice fill in the blank type question. This will be your question.' \
                                                                                Provide also the Russian Cyrilic translation of the question. \
                                                                                Include the removed word among the answers. \
                                                                                The rest of the answers should be identical or transformed or conjugated versions of the words {word2},{word3},{word4}. \
                                                                                The instruction part of the question should be in Russian Cyrilic as the persons english is very limited.\nFormatting Instructions: {format_instructions}")
            
            human_message_prompt = HumanMessagePromptTemplate.from_template("{user_input}")

            chat_prompt = ChatPromptTemplate(messages=[system_message_prompt, human_message_prompt])

            chain = LLMChain(llm=chat, prompt=chat_prompt, output_parser=output_parser)

            sample = self.word_frame.sample(4)
            
            response = chain.run(user_input="Give me a multiple choice fill in the blank type question so I can practice english", format_instructions=output_parser.get_format_instructions(), word1=sample['word'].iloc[0],
                                word2=sample['word'].iloc[1], word3=sample['word'].iloc[2], word4=sample['word'].iloc[3])

        elif questionType == 1:

            variant_list = ["tenses", "forming negative sentences in various tenses","forming yes/no questions in various tenses"]
            variant = random.choice(variant_list)

            system_message_prompt = SystemMessagePromptTemplate.from_template("Human is a native russian who is trying to learn english. \
                                                                              Humans english level is A2. \
                                                                              Construct a multiple choice fill in the blank type question about {variant} of the verb: {verb}. \
                                                                              Provide also the Russian Cyrilic translation of the question. \
                                                                                The instruction part of the question should be in Russian Cyrilic as the persons english is very limited.\nFormatting Instructions: {format_instructions}")
            
            human_message_prompt = HumanMessagePromptTemplate.from_template("{user_input}")

            chat_prompt = ChatPromptTemplate(messages=[system_message_prompt, human_message_prompt])

            chain = LLMChain(llm=chat, prompt=chat_prompt, output_parser=output_parser)
            
            response = chain.run(user_input="Give me a multiple choice fill in the blank type question so I can practice english", format_instructions=output_parser.get_format_instructions(),
                                 verb=random.choice(common_verbs), variant=variant)
            
        elif questionType == 2:

            system_message_prompt = SystemMessagePromptTemplate.from_template("Human is a native russian who is trying to learn english. \
                                                                              Humans english level is B1. \
                                                                              construct a multiple choice fill in the blank type question that tests the knowledge of the meaning and the usage of the word: {word}. \
                                                                              Please make sure that there's only one correct answer. \
                                                                              Provide also the Russian Cyrilic translation of the question. \
                                                                              The instruction part of the question should be in Russian Cyrilic as the persons english is very limited.\nFormatting Instructions: {format_instructions}")
            
            human_message_prompt = HumanMessagePromptTemplate.from_template("{user_input}")

            chat_prompt = ChatPromptTemplate(messages=[system_message_prompt, human_message_prompt])

            chain = LLMChain(llm=chat, prompt=chat_prompt, output_parser=output_parser)

            sample = self.word_frame.sample(1)
            
            response = chain.run(user_input="Give me a multiple choice fill in the blank type question so I can practice english", format_instructions=output_parser.get_format_instructions(), word=sample['word'].iloc[0])

        response_string = ""

        response_string = response["instructions"] + "\n"  + response["sentence"] + "\n"  + response["sentence_in_russian"] + "\n" + "1) " +response["choice1"] + "\n" + "2) " +response["choice2"] + "\n" + \
        "3) " + response["choice3"] + "\n" + "4) " + response["choice4"]

        self.correct_choice = response["choice" + str(response["correct_choice"])]
        self.explanation = response["explanation"]
        self.bot_mode = BotMode.LANGUAGE_GAME

        return response_string

    def generate_example_sentences(self, text: str) -> str:

        if self.bot_mode == BotMode.EXAMPLE_SENTENCES:

            output_parser = JsonOutputParser(pydantic_object=Translation)

            #print(format_instructions)

            system_message_prompt = SystemMessagePromptTemplate.from_template("Generate five english sentences and \
            their russian translations in cyrilic letters for the word provided by the human.\
            \nFormatting Instructions: {format_instructions}")

            human_message_prompt = HumanMessagePromptTemplate.from_template("{user_input}")


            chat_prompt = ChatPromptTemplate(messages=[system_message_prompt, human_message_prompt])

            chain = LLMChain(llm=chat, prompt=chat_prompt, output_parser=output_parser)
            
            response = chain.run(user_input=text, format_instructions=output_parser.get_format_instructions())

            response_string = ""

            for index, item in enumerate(response):
                response_string = response_string + "• " + item['english_sentence'] + "\n"
                response_string = response_string + "• " + item['russian_sentence'] + "\n"

                if index< 4:
                    response_string = response_string + "\n"

            return response_string

        if self.bot_mode == BotMode.LANGUAGE_GAME:

            return self.generate_test_string()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_type: str = update.message.chat.type
        text: str = update.message.text.lower()

        text = text.replace("’", "'")

        print(f'User ({update.message.chat.id}) in: {message_type}: "{text}"')

        if self.bot_mode == BotMode.LANGUAGE_GAME:
            if text == self.correct_choice.lower():
                await update.message.reply_text("Поздравляю!🎉🎉🍾" + " " + self.explanation)
                answer_status = True
            else:
                await update.message.reply_text("Извините, это неверный ответ. Правильный ответ: " + str(self.correct_choice) + " " + self.explanation)
                answer_status = False

            data = {
            'datetime': dt.datetime.now().strftime('%Y-%m-%d'),
            'answer_status': answer_status
            }
            data_list = [data]

    # Open the JSON file in write mode

            performance_file_name = 'performance_history.json'

            if os.path.exists(performance_file_name):
                with open('performance_history.json', 'r') as f:
                    data_list = json.load(f)
                    data_list.append(data)
            else:
                data_list = [data]

            with open('performance_history.json', 'w') as f:
            # Dump the dictionary to the JSON file
                json.dump(data_list, f, indent=4)
        
        elif self.bot_mode == BotMode.EXAMPLE_SENTENCES:

            response = self.generate_example_sentences(text)
            await update.message.reply_text(response)


        # if message_type == 'group':
        #     if BOT_USERNAME in text:
        #         new_text: str = text.replace(BOT_USERNAME,'').strip()
        #         response: str = self.handle_response(new_text)
        #     else:
        #         return
        # else:
        #     response: str = self.handle_response(text)

        # print('Bot:', response)
        # await update.message.reply_text(response)

    def generate_performance_string(self):

        with open('performance_history.json', 'r') as f:
            performance_data = json.load(f)

        performance_frame = pd.DataFrame(performance_data)

        today = dt.datetime.today()

        last_week_start = today - dt.timedelta(days=7)
        last_week_dates = [last_week_start + dt.timedelta(days=i) for i in range(7)]
        last_week_dates_array = pd.to_datetime(last_week_dates)
        last_week_dates_array = last_week_dates_array.strftime('%Y-%m-%d')

        number_of_missed_dates = len(set(last_week_dates_array)-set(performance_frame['datetime']))

        if number_of_missed_dates == 0:
            consistency_string = "На прошлой неделе ты ответила на вопросы каждый день. Продолжайте в том же духе.👍👌"
        else:
            consistency_string = f"На прошлой неделе ты ответила на вопросы по {7-number_of_missed_dates} дням недели. Я думаю, ты можешь быть более последовательна."

        
        num_questions_answered = len(performance_frame)
        num_correct_answers = len(performance_frame[performance_frame['answer_status']])
        correct_percentage = round((num_correct_answers / num_questions_answered) * 100)

        if correct_percentage >= 90:
            performance_string = f"Поздравляю! 🍾🎉👍👍😎 Пока что ты ответила на {num_questions_answered} вопросов, и твой процент правильных ответов составляет {correct_percentage}%."
        else:
            performance_string = f"Пока что ты ответила на {num_questions_answered} вопросов, и твой процент правильных ответов составляет {correct_percentage}%."

        return {'performance_string': performance_string, 'consistency_string': consistency_string}

load_dotenv(find_dotenv())
TOKEN = os.getenv('RUSSIAN_TEACHER_TELEGRAM_BOT_TOKEN')
BOT_USERNAME = os.getenv('RUSSIAN_TEACHER_TELEGRAM_BOT_USERNAME')

bot_mode = BotMode.EXAMPLE_SENTENCES;
chat = ChatGoogleGenerativeAI(model="gemini-1.5-pro")


#Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Thanks for chatting with me! I am an English Teacher!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Please type something so I can respond')

    
class Translation(BaseModel):
    english_sentence: str = Field(description="This is the english sentence")
    russian_sentence: str = Field(description="This is the russian sentence in cyrilic")

class MultipleChoiceQuestion(BaseModel):
    instructions: str = Field(description="This is the instructions in Russian Cyrilic")
    sentence: str = Field(description="This is the sentence with a blank in English")
    sentence_in_russian: str = Field(description="This is the translation of the sentence in Russian Cyrilic")
    choice1: str = Field(description="This is the first choice")
    choice2: str = Field(description="This is the second choice")
    choice3: str = Field(description="This is the third choice")
    choice4: str = Field(description="This is the fourth choice")
    correct_choice: int = Field(description="This is the index of the correct choice")
    explanation: str = Field(description="This is the explanation of the correct choice in Russian Cyrilic")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update "{update}" caused error {context.error}')


def main():
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()
    job_queue = app.job_queue
    
    chat_id = os.getenv('RUSSIAN_STUDENT_TELEGRAM_CHAT_ID')

    teacher_bot = TeacherBot()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('examples',teacher_bot.example_sentences))
    app.add_handler(CommandHandler('game',teacher_bot.game))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, teacher_bot.handle_message))

    # Errors
    app.add_error_handler(error)

    async def send_message(context: ContextTypes.DEFAULT_TYPE):
        test_string = teacher_bot.generate_test_string()
        performance_output = teacher_bot.generate_performance_string()
        performance_string = performance_output['performance_string']
        consistency_string = performance_output['consistency_string']
        await context.bot.send_message(chat_id=chat_id, text="Привет, Алина😃")
        await context.bot.send_message(chat_id=chat_id, text=consistency_string)
        await context.bot.send_message(chat_id=chat_id, text=performance_string)
        await context.bot.send_message(chat_id=chat_id, text=test_string)

    tz = pytz.timezone('America/New_York')

    # Get the current time in the specified timezone
    current_time = dt.datetime.now(tz)
    future_time = current_time + dt.timedelta(seconds=10)
    print(future_time.timetz())
    job_queue.run_daily(send_message, future_time.timetz(), days=[0, 1, 2, 3, 4, 5, 6])
 

    #Polls the bot
    # print('Polling...')
    # app.run_polling(poll_interval=3)    
    # Start polling

    #await app.initialize()
    print('Polling...')
    # await app.start()
    # await app.updater.start_polling(poll_interval=3)
    # await app.initialize()
    # await app.start()
    # await asyncio.Event().wait() 

    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()

    