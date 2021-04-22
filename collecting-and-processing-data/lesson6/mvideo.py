from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pprint import pprint


URL = 'https://www.mvideo.ru/'


driver = webdriver.Chrome('./chromedriver')
driver.get(URL)
assert 'М.Видео' in driver.title
modal_window = False

# Борьба с модальным окном
try:
    WebDriverWait(driver, 10). \
                until(EC.frame_to_be_available_and_switch_to_it('fl-212563'))
    modal_window = True
except Exception as e:
    print('Окна не было', e)
    pass

if modal_window:
    WebDriverWait(driver, 10). \
        until(EC.presence_of_element_located((By.CLASS_NAME, 'close'))).click()
driver.switch_to.default_content()
hits_block = driver.find_element_by_class_name('sel-hits-block')

next_btn_disabled = ''

# Нажимаем кнупку далее, пока это возможно.
while next_btn_disabled.find('disabled') == -1:
    next_button = WebDriverWait(hits_block, 10).\
        until(EC.presence_of_element_located((By.CLASS_NAME, 'sel-hits-button-next')))
    next_button.send_keys(Keys.ENTER)
    next_btn_disabled = next_button.get_attribute('class')

hits_items = hits_block.find_elements_by_class_name('gallery-list-item')

hits_list = []

# Теперь просто парсим ХТМЛ и все готово.

for item in hits_items:
    item_name = item.find_element_by_tag_name('h4').get_attribute('title')
    item_curr_price = item.find_element_by_css_selector('div.c-pdp-price__current').get_attribute('innerHTML')
    item_old = item.find_element_by_css_selector('span.c-pdp-price__old').get_attribute('innerHTML')
    hits_list.append({
        'name': item_name,
        'price': int(''.join([s for s in item_curr_price if s.isdigit()])),
        'old': int(''.join([s for s in item_old if s.isdigit()]))
    })

pprint(hits_list)
