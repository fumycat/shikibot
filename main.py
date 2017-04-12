import os
import uuid

import requests as http
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, CallbackQueryHandler

API = 'https://shikimori.org/api/'
SEARCH_LIMIT = 30  # must be <= 50


def escapize(text):
    return text.replace('&', '&amp;') \
        .replace('<', '&lt;') \
        .replace('>', '&gt;')


def start(bot, update):
    update.message.reply_text('Введите <code>@shikibot ЗАПРОС</code> в строке набора, чтобы найти аниме \nПример:\n@shikibot lucky star\n\nЭтот бот использует апи сайта shikimori.org\nАвтор: @fumycat', parse_mode='HTML')


def inline_query(bot, update):
    query = update.inline_query.query
    if query == '':
        return
    print('inline query -', query)
    inline_results = list()

    search_results = http.get('{}animes?limit={}&search={}'.format(API, SEARCH_LIMIT, query)).json()

    for result in search_results:
        description = result['kind'].title() + ' - ' + str(result['episodes'])
        text = '<b>' + result['russian'] + '</b>\nhttps://shikimori.org' + result['url']
        inline_results.append(
            InlineQueryResultArticle(type='article',
                                     id=uuid.uuid4(),
                                     title=result['russian'],
                                     description=description,
                                     input_message_content=InputTextMessageContent(text, parse_mode='HTML'),
                                     reply_markup=kb(str(result['id'])),
                                     thumb_url='https://shikimori.org' + result['image']['preview']))
    print('ready')
    print(bot.answerInlineQuery(update.inline_query.id, results=inline_results, cache_time=600))


def button(bot, update):
    info = http.get('{}animes/{}'.format(API, update.callback_query.data)).json()
    ep_info = 'Эпизоды: {}'.format(info['episodes']) if info['episodes'] == info['episodes_aired'] else\
        'Эпизоды: {}/{}'.format(info['episodes_aired'], info['episodes'] if str(info['episodes']) != '0' else '∞')

    result = '<b>{name}</b> <i>({stars}/10)</i>\n<i>{genre}\n{ep}\n{dur}</i>\n\n{text}'.format(
        name=escapize(info['russian']),
        stars=info['score'],
        genre=', '.join([g['russian'] for g in info.get('genres', [])]),
        ep=ep_info,
        dur='Длительность эпизода: {} мин.'.format(info['duration']),
        text=escapize(info['description'])
    )
    bot.editMessageText(message_id=update.callback_query.inline_message_id,
                        text=result,
                        parse_mode='HTML')


def kb(data):
    keyboard = [InlineKeyboardButton(text='Описание', callback_data=data)]
    return InlineKeyboardMarkup(keyboard)


if __name__ == '__main__':
    TOKEN = os.environ.get('TOKEN')
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    updater.start_webhook(listen="0.0.0.0", port=int(os.environ.get('PORT', '5000')), url_path=TOKEN)
    updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(os.environ.get('APP'), TOKEN))

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(InlineQueryHandler(inline_query))

    updater.idle()
