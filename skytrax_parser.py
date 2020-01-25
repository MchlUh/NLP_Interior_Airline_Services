from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd

link_file_name = 'skytrax_reviews_links.txt'
data_file_name = 'skytrax_reviews_data.csv'

# Makes selenium open Chrome in background
chrome_options = Options()  
chrome_options.add_argument("--headless") 


def get_links():
    links = list()
    browser = webdriver.Chrome(chrome_options=chrome_options)
    for review_link in ['https://www.airlinequality.com/review-pages/a-z-{review_type}-reviews/'
                        .format(review_type=review_type) for review_type in ('airline', 'seat')]:
        browser.get(review_link)
        airline_lists = [airline_list.find_elements_by_tag_name('li')
                         for airline_list in browser.find_elements_by_class_name('items')]
        for airline_list in airline_lists:
            for airline in airline_list:
                link = airline.find_element_by_tag_name('a').get_attribute('href')
                links.append(link)
    browser.close()
    # Save unique links in text file
    link_file = open(link_file_name, 'wt')
    link_file.write('\n'.join(set(links)))


links = open(link_file_name).read().split('\n')
try:
    data = pd.read_csv(data_file_name, index_col=None)
except FileNotFoundError:
    data = pd.DataFrame()
    data.to_csv(data_file_name)

for link in links[220:250]:  # TODO DEL
    browser = webdriver.Chrome(chrome_options=chrome_options)
    browser.get(link + '/?sortby=post_date%3ADesc&pagesize=10000')  # show all reviews in one page
    airline_name = browser.find_element_by_class_name('info').find_element_by_tag_name('h1').text
    review_type = browser.find_element_by_class_name('info').find_element_by_tag_name('h2').text
    if review_type in data[data.airline == airline_name].review_type:
        print('Already scraped {review_type} for {airline_name}'
              .format(review_type=review_type, airline_name=airline_name))
        continue
    print('Scraping {}'.format(airline_name))
    reviews_container = browser.find_element_by_tag_name('article')
    reviews = reviews_container.find_elements_by_tag_name('article')
    data_lines = []
    for review in reviews:
        data_line = {'airline': airline_name, 'review_type': review_type}
        try:
            data_line['rating'], data_line['best_rating'] = review.find_element_by_class_name('rating-10').text.split('/')
        except ValueError:
            pass
        data_line['header'] = review.find_element_by_class_name('text_header').text
        data_line['comment_date'] = review.find_element_by_tag_name('time').get_attribute('datetime')
        data_line['comment'] = review.find_element_by_class_name('text_content').text
        ratings_table = review.find_element_by_class_name('review-ratings').find_element_by_tag_name('tbody')
        for rating in ratings_table.find_elements_by_tag_name('tr'):
            try:
                key_value = rating.find_elements_by_tag_name('td')
                if 'stars' in key_value[1].get_attribute('class'):
                    number_of_stars = len(key_value[1].find_elements_by_class_name('star.fill '))
                    data_line[key_value[0].text] = number_of_stars
                else:
                    data_line[key_value[0].text] = key_value[1].text
            except Exception:
                pass
        data_lines.append(data_line)
    browser.close()
    data = data.append(pd.DataFrame(data_lines))
    data.to_csv(data_file_name, index=None)

