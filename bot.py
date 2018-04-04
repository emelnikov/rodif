#!/home/ubuntu/virtualenvs/rodif/bin/python3
import configparser
import re
import imaplib
import email
from telepot import Bot
from telepot.loop import MessageLoop
from time import sleep

class Rodif():
    def __init__(self):
        self.config = configparser.RawConfigParser()
        self.config.read('config.conf')
        self.allowed = self.config['General']['allowed'].replace(' ', '').split(',')
        self.token = self.config['General']['telegram_token']
        self.participants = self.config['General']['participants'].replace(' ', '').split(',')
        self.bot = Bot(self.token)
        MessageLoop(self.bot, self.handle).run_as_thread()
        self.imap()

    def handle(self, msg):
        message_body = msg['text']
        if str(msg['chat']['id']) in self.allowed:
            if message_body[0] == "/":  # then it's command!
                if message_body[1:7] == 'ticket':
                    self.bot.sendMessage(msg['chat']['id'], 'We have new ticket, %s' % ', '.join(self.participants))
                    #Send a link
                    #CHANGE TO JIRA TAG
                    if re.search(r'FCSD\-\d*$', message_body):
                        self.bot.sendMessage(msg['chat']['id'], self.config['General']['jira'] + re.search(r'FCSD\-\d*$', message_body).group(0))
                elif message_body[1:6] == 'addme':
                    try:
                        if len(self.config['General']['participants'].replace('@%s' % msg['from']['username'],'')) != len(self.config['General']['participants']):
                            self.bot.sendMessage(msg['chat']['id'], 'You are already in the list.')
                        else:
                            self.config.set('General', 'participants', self.config['General']['participants'] + '%s@%s' % (', ' if self.config['General']['participants'] else '', msg['from']['username']))
                            with open('config.conf', 'w') as configfile:
                                self.config.write(configfile)
                                self.read_config()
                            self.bot.sendMessage(msg['chat']['id'], '@%s has been added.' % msg['from']['username'])
                    except Exception as e:
                        self.bot.sendMessage(msg['chat']['id'], 'I cannot add you to the list becuase of some issue.')
                elif message_body[1:13] == 'participants':
                    try:
                        self.bot.sendMessage(msg['chat']['id'], self.config['General']['participants'])
                    except Exception as e:
                        self.bot.sendMessage(msg['chat']['id'], 'No users in the list.')
                        print(e)
        return

    def read_config(self):
        self.participants = self.config['General']['participants'].replace(' ', '').split(',')

    def imap(self):
        sleep_seconds = int(self.config['General']['sleep'])
        email_prev = False
        while True:
            try:
                mail = imaplib.IMAP4_SSL(self.config['General']['imap_address'])
                mail.login(self.config['General']['imap_login'], self.config['General']['imap_password'])
                while True:
                    mail.list()
                    mail.select(self.config['General']['jira_imap_label'])  # connect to imap folder.

                    result, data = mail.search(None, 'UNSEEN')

                    if result == 'OK':
                        for num in data[0].split():
                            retcode, message = mail.fetch(num,'(RFC822)')
                            parsed_message = email.message_from_bytes(message[0][1])
                            subject = email.header.decode_header(parsed_message['subject'])
                            try:
                                if subject[0][1] is None:
                                    subject_string = subject[0][0]
                                else:
                                    subject_string = subject[0][0].decode(subject[0][1])
                            except Exception as e:
                                print(e)
                            # print(subject_string)
                            self.bot.sendMessage(self.config['General']['allowed'], 'New ticket: ' + subject_string)
                            # mail.store(num, '-FLAGS', '\Seen')
                            sleep(sleep_seconds)
                mail.close()
            except Exception as e:
                print(e)
                sleep(sleep_seconds)
                continue

Rodif()

while True:
    sleep(10)
