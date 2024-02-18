import scrapy
from bs4 import BeautifulSoup
import csv
import scrapy
import os
import pandas as pd
import json
from urllib.parse import unquote

KEYWORDS = ['python']

# , 'data%20scientist'
# not yet : , 'data%20engineer', 'machine%20learning%20engineer', 'artificial%20intelligence%20engineer'

class LinkedinJobDescriptionSpider(scrapy.Spider):
    name = "linkedin_job_description"
    
    keywords = KEYWORDS #'software_engineer'

    # job_pages = ["https://www.linkedin.com/jobs/view/python-developer-internship-at-mindpal-3703089625?refId=w8fjclBo8vHOKvOm6qTGIA%3D%3D&trackingId=11l%2BLLmpE5BEVgxUIhaY2A%3D%3D&position=19&pageNum=0&trk=public_jobs_jserp-result_search-card"]

    def start_requests(self):
        job_index_tracker = 7
        first_keyword = 0

        keyword = unquote(self.keywords[first_keyword]).replace('%2B', '_')

        self.readUrlsFromJobsFile(keyword)
        first_url = self.job_pages[job_index_tracker]

        yield scrapy.Request(url=first_url, callback=self.parse, meta={'job_index_tracker': job_index_tracker, 'first_keyword': first_keyword})
        


    def parse(self, response):

        job_index_tracker = response.meta['job_index_tracker']
        first_keyword = response.meta['first_keyword']
        keyword = unquote(self.keywords[first_keyword]).replace('%2B', '_')

        print('***************')
        print('****** Scraping page ' + str(job_index_tracker+1) + ' of ' + str(len(self.job_pages)) + ' for keyword ' + keyword + ' ******')
        print('***************')

        job_item = {}

        url_parts = response.url.split('/')
        jobs_index = url_parts.index('view')
        job_code = url_parts[jobs_index + 1].split("?refId")[0]
        job_id = job_code.split('-')[-1]

        # Extract job basic details
        job_item['job_id'] = job_id

        # print(response.text)
        try:
            job_item['job_title'] = response.css("h1::text").get(default='not-found').strip()
            job_item['job_link'] = response.url
            job_item['company_name'] = response.css('.topcard__org-name-link::text').get(default='not-found').strip()
            job_item['company_link'] = response.css('.topcard__org-name-link::attr(href)').get(default='not-found').strip()
            job_item['job_location'] = response.css('.topcard__flavor--bullet::text').get(default='not-found').strip()

            script_content = response.xpath('//script[@type="application/ld+json"]/text()').get()
            soup = BeautifulSoup(script_content, 'html.parser')
            description_html = soup.get_text()
            description_data = json.loads(description_html)
            job_item['date_posted'] = description_data['datePosted']
            job_item['job_description'] = description_data['description']
        
        except TypeError:
            self.logger.warning("Script content is None. Skipping parsing.")
        except IndexError:
            self.logger.warning("Index out of range. Skipping parsing.")

        job_item['search_keywords'] = keyword
        job_item['job_code'] = job_code

        self.save_to_csv(job_item)

        yield job_item

        job_index_tracker = job_index_tracker + 1

        if job_index_tracker <= (len(self.job_pages)-1):
            next_url = self.job_pages[job_index_tracker]
            yield scrapy.Request(url=next_url, callback=self.parse, meta={'job_index_tracker': job_index_tracker, 'first_keyword': first_keyword})
        else:
            first_keyword = first_keyword + 1
            if first_keyword < len(self.keywords):
                job_index_tracker = 0
                self.readUrlsFromJobsFile(unquote(self.keywords[first_keyword]).replace('%2B', '_'))
                next_url = self.job_pages[job_index_tracker]
                yield scrapy.Request(url=next_url, callback=self.parse, meta={'job_index_tracker': job_index_tracker, 'first_keyword': first_keyword})
            else:
                print('***************')
                print('****** Finished scraping all jobs ******')
                print('***************')


    def save_to_csv(self, item):
        # Define the output directory where CSV files will be saved
        output_dir = 'data/{}'.format(item['search_keywords'])

        # Ensure the output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Define the CSV filename based on a unique identifier in the item
        filename = os.path.join(output_dir, f'{item["job_code"]}.csv')  # Assuming 'title' exists in the item
        df = pd.DataFrame([item])

        df.to_csv(filename, index=False)

    def readUrlsFromJobsFile(self, keyword):
        filename = os.path.join('data_url', '{}.csv'.format(keyword)) 
        self.job_pages = []
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for job in reader:
                if job['url'] != 'not-found':
                    self.job_pages.append(job['url'])
            
        #remove any duplicate links - to prevent spider from shutting down on duplicate
        self.job_pages = list(set(self.job_pages))


