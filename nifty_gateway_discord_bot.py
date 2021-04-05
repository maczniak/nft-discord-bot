#!/usr/bin/env python3

import logging
import signal
import sys
import time

from discord_webhook import DiscordWebhook, DiscordEmbed
import schedule
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def sigint_handler(sig, frame):
  driver.quit()
  sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

URL = 'https://niftygateway.com/collections'
webhook_url = 'https://discord.com/api/webhooks/................../.................................................WEBHOOK.URL.HERE...'

def make_chrome():
  options = webdriver.ChromeOptions()
  options.add_argument('headless')
  return webdriver.Chrome(executable_path='./chromedriver', options=options)

driver = make_chrome()
last_titles = None
last_infos = None

def notify(drop):
  title, infos = drop
  webhook = DiscordWebhook(url = webhook_url, \
                           username = 'Nifty Gateway | ' + title)
  for info in infos:
    embed = DiscordEmbed(title = info['description'], \
                   description = 'by ' + info['artist'] + '\n' + info['link'], \
                   color = '03b2f8')
    embed.set_image(url = info['image'])
    embed.set_timestamp()
    webhook.add_embed(embed)
  response = webhook.execute()

def difference(last, now):
  last_titles, last_infos = last
  titles, infos = now
  diffs = []
  for title, info in zip(titles, infos):
    if title == last_titles[0]:
      return diffs
    diffs.append((title, info))
  return diffs

def check_new_drops():
  global driver, last_titles, last_infos
  
  logging.info(time.strftime('%x %X'))
  try:
    driver.get(url=URL)
  except Exception: # selenium.common.exceptions.WebDriverException
    logging.exception('driver exception')
    driver = make_chrome()
    return
  try:
    WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.CLASS_NAME, 'MuiTypography-alignCenter')))
  except Exception: # selenium.common.exceptions.TimeoutException
    logging.exception('wait exception')
    return

  title_elements = driver.find_elements_by_xpath('//*[@id="root"]/div/div/div/span')
  titles = [e.text for e in title_elements]
  body_elements = [e.find_elements_by_xpath('ancestor::div/following-sibling::div[1]/div/div') for e in title_elements]
  infos = []
  for ell in body_elements:
    subinfos = []
    for el in ell:
      link = el.find_element_by_xpath('div[1]/a').get_attribute('href')
      _image = el.find_element_by_xpath('div[1]/a/div/div').get_attribute('style')
      image = _image[_image.index('("') + len('("'):_image.index('")')]
      artist = el.find_element_by_xpath('div[2]/div/div/p[1]').text
      description = el.find_element_by_xpath('div[2]/div/div/p[2]').text
      subinfos.append({
        'link':        link,
        'image':       image,
        'artist':      artist,
        'description': description
      })
    infos.append(subinfos)
  if last_titles:
    diffs = difference((last_titles, last_infos), (titles, infos))
    if diffs:
      [notify(diff) for diff in diffs]
      logging.info(diffs)
  last_titles, last_infos = titles, infos

schedule.every().minutes.at(':00').do(check_new_drops)

while True:
  schedule.run_pending()
  time.sleep(1)

