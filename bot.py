from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackContext, ConversationHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update, ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
import logging
from parser import Parser

# def start(update, context):
#     context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
#     print('test it!')

class Bot:
    def __init__(self):

        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
        )
        self.logger = logging.getLogger("WB Bot Logger")

        self.DISCOUNT, self.OPTIONS = range(2)

        # Create the Updater and pass it your bot's token.
        self.updater = Updater(token='1934217722:AAEmDIq4bZkN1lJg1d2pcUvBD1K1t76T8z8', use_context=True)

        # Get the dispatcher to register handlers
        self.dispatcher = self.updater.dispatcher

        # self.chat_data = []

    def start(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        update.message.reply_markdown_v2(
            fr'Hi {user.mention_markdown_v2()}\!',
                              reply_markup=self.markup
        )
        context.bot.send_message(chat_id=update.effective_chat.id, text='Type /help for possible commands')

    # def add_suggested_actions(self, update, context):
    #     options = []
    #
    #     options.append(InlineKeyboardButton('Enter Name', callback_data='name'))
    #     options.append(InlineKeyboardButton('Enter Age', callback_data='age'))
    #
    #     reply_markup = InlineKeyboardMarkup([options])
    #
    #     context.bot.send_message(chat_id=update.effective_chat.id, text='Choose an option', reply_markup=reply_markup)
    # Что-то такое нужно добавить для обработки ответов: updater.dispatcher.add_handler(CallbackQueryHandler(add_suggested_actions, pattern='m*'))

    def error(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Error occured, see logs for details')
        print(f'Update {update.message["text"]} caused error: {context.error}')

    # def set_discount(self, update, context):
    #     self.current_discount = int(''.join(context.args))
    #     print(self.current_discount)
    #     context.bot.send_message(chat_id=update.effective_chat.id, text=f'Current discount now is {self.current_discount}')

    def unknown(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

    def brute_force_stop(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Bot now stops")
        try:
            self.updater.stop()
        except Exception as error:
            self.logger.error(f'brute_froce_stop error: {error}')

    def help_command(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /help is issued."""
        update.message.reply_text(
                                  '/start - Default start\n'
                                  '/parser - Start parser dialogue\n'
                                  '/close - Close keyboard \n'
                                  '/super discount - Create parser and run update_prices with provided discount\n'
                                  )

    def initiate_start_parser(self, update, context):

        # self.current_discount = int(''.join(context.args))
        # print('Set current discount:', self.current_discount)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Please, enter current WB discount', reply_markup=ReplyKeyboardRemove())
        return self.DISCOUNT

    # def start_parser(self, update, context):
    #     try:
    #         self.current_discount = int(update.message.text)
    #         self.parser = Parser(self.current_discount)
    #     except Exception as error:
    #         context.bot.send_message(chat_id=update.effective_chat.id,
    #                                  text='Error occured, see logs for details')
    #         print(error)
    #         # update.message.reply_text('Error occured, see logs for details')
    #     else:
    #         update.message.reply_text(f'Parser started with current WB discount {self.current_discount}. \nType /update to update prices, /show to show currenty')

    def update_prices(self, update, context):
        if not self.parser:
            raise Exception
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Updating of prices initiated ok')
            try:
                self.parser.update_prices()
            except Exception as error:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Error occured in command /update, see logs for details. Rerun /parser command')
                print(error)
                return ConversationHandler.END
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Prices updated ok')
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Rerun /parser to do smth else')
                return ConversationHandler.END

    def show_items(self, update, context):
        if not self.parser:
            raise Exception
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Showing of items initiated ok')
            try:
                items = self.parser.get_db_data()
                items_to_bot = items.loc[0:, ['articul', 'my_title', 'min_my_price', 'url']].to_markdown(index=False)
                print(items_to_bot)
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=items_to_bot)
            except Exception as error:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Error occured in command /show, see logs for details. Rerun /parser', reply_markup=self.markup)
                print(error)
                return ConversationHandler.END
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Items shown ok. Rerun /parser to do smth else', reply_markup=self.markup)
                return ConversationHandler.END
    def super(self, update, context):
        self.current_discount = int(''.join(context.args))
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Update prices initiated ok with current discount of {self.current_discount}')
        try:
            self.parser = Parser(self.current_discount)
            self.parser.update_prices()
        except:
            print('Trying to log "except"')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Update prices finished ok')
    def close_keyboard(self, update, context):
        update.message.reply_text('Ok', reply_markup=ReplyKeyboardRemove())

    # def task(self, context):
    #     context.bot.send_message(context.job.context, text='Хорош сидеть за компьютером, разомнись!')

    # def set_timer(self, update, context):
    #
    #     # создаём задачу task в очереди job_queue
    #     # передаём ей идентификатор текущего чата
    #     # идентификатор далее будет доступен через job.context
    #
    #     delay = 5  # количество секунд
    #     job = context.job_queue.run_once(self.task, delay, context=update.message.chat_id)
    #
    #     # Регистрируем созданную задачу в пользовательских данных
    #     context.chat_data['job'] = job
    #
    #     # Сообщаем о том, что таймер установлен
    #     update.message.reply_text('Таймер установлен на ' + str(delay) + ' секунд')
    #
    # def unset_timer(self, update, context):
    #     # Проверяем, что задача действительно установлена
    #     if 'job' in context.chat_data:
    #         # планируем удаление задачи
    #         context.chat_data['job'].schedule_removal()
    #         # и очищаем пользовательские данные
    #         del context.chat_data['job']
    #
    #     update.message.reply_text('Таймер отменён!')

    def add_item(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Add items function is to be developed. Rerun /parser to do smth else')
        return ConversationHandler.END

    # def parser(self, update, context):
    #
    #     context.bot.send_message(chat_id=update.effective_chat.id, text=f'Please, choose what you want to do: /update /show /add')
    #     return OPTIONS

    def start_parser(self, update, context):
        self.current_discount = int(update.message.text)
        try:
            self.current_discount = int(update.message.text)
            self.parser = Parser(self.current_discount)
        except Exception as error:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Error occured, see logs for details')
            print(error)
            # update.message.reply_text('Error occured, see logs for details')
        else:
            update.message.reply_text(f'Parser started with current WB discount {self.current_discount}. \nType /update to update prices, /show to show current, /add to add new item', reply_markup=self.parser_markup)
            return self.OPTIONS

    def cancel(self, update: Update, context: CallbackContext) -> int:
        """Cancels and ends the conversation."""
        user = update.message.from_user
        self.logger.info("User %s canceled the conversation.", user.first_name)
        update.message.reply_text(
            'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
        )

        return ConversationHandler.END
# updater.idle()

    def main(self) -> None:
        """Start the bot."""
        self.reply_keyboard = [['/start', '/help', '/close', '/parser']]

        self.markup = ReplyKeyboardMarkup(self.reply_keyboard, one_time_keyboard=False)

        self.parser_keyboard = [['/cancel', '/update', '/show', '/add', '/parser']]
        self.parser_markup = ReplyKeyboardMarkup(self.parser_keyboard, one_time_keyboard=False)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('parser', self.initiate_start_parser)],
            states={
                # INIT: [MessageHandler(Filters.regex('^(Boy|Girl|Other)$'), gender)],
                self.DISCOUNT: [MessageHandler(Filters.text, self.start_parser)],
                self.OPTIONS: [
                      CommandHandler('update', self.update_prices),
                      CommandHandler('show', self.show_items),
                      CommandHandler('add', self.add_item)
                      ]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)], allow_reentry=True
        )
        self.dispatcher.add_handler(conv_handler)
        # on different commands - answer in Telegram
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        # self.dispatcher.add_handler(CommandHandler("add", self.add_suggested_actions))
        self.dispatcher.add_handler(CommandHandler("help", self.help_command))
        self.dispatcher.add_handler(CommandHandler("stop", self.brute_force_stop))
        # self.dispatcher.add_handler(CommandHandler("start_again", self.brute_force_start))
        # self.dispatcher.add_handler(CommandHandler('discount', self.set_discount))
        self.dispatcher.add_handler(CommandHandler("parser", self.initiate_start_parser))
        self.dispatcher.add_handler(CommandHandler("update", self.update_prices))
        self.dispatcher.add_handler(CommandHandler("show", self.show_items))
        self.dispatcher.add_handler(CommandHandler("super", self.super))
        self.dispatcher.add_handler(CommandHandler("close", self.close_keyboard))
        # self.dispatcher.add_handler(CommandHandler("set_timer", self.set_timer, pass_job_queue=True, pass_chat_data=True))
        # self.dispatcher.add_handler(CommandHandler("unset_timer", self.unset_timer, pass_chat_data=True))

        # on non command i.e message - echo the message on Telegram
        self.dispatcher.add_handler(MessageHandler(Filters.command, self.unknown))
        self.dispatcher.add_handler(MessageHandler(Filters.text, self.start_parser))

        self.dispatcher.add_error_handler(self.error)

        # Start the Bot
        self.updater.start_polling()
        self.updater.idle()

if __name__ == '__main__':
    bot = Bot()
    bot.main()
