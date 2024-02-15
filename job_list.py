import scrapy
from urllib.parse import unquote
import os
import pandas as pd
import csv
import settings

class LinkedJobsSpider(scrapy.Spider):
    name = "linkedin_jobs"
    api_url_template = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={}&location=United%2BStates&geoId=103644278&trk=public_jobs_jobs-search-bar_search-submit&start={}'
    keywords = settings.KEYWORDS
    numOfJobs = settings.NUM_JOBS

    def start_requests(self):

        first_keyword = 0

        first_job_on_page = 0  

        url = self.api_url_template.format(self.keywords[first_keyword], first_job_on_page)
        yield scrapy.Request(url=url, callback=self.parse_job, meta={'first_job_on_page': first_job_on_page, 'first_keyword': first_keyword})


    def parse_job(self, response):
        first_job_on_page = response.meta.get('first_job_on_page')
        first_keyword = response.meta.get('first_keyword')

        search_keywords = self.keywords[first_keyword].unquote().replace('%2B', '_')
  
        jobs = response.css("li")

        num_jobs_returned = len(jobs)
        print(f"******* Num Jobs Returned for start={first_job_on_page} of keyword={search_keywords} *******")
        print(num_jobs_returned)
        print('*****')

        urls = []

        for job in jobs:

            url_item = {
                'url': job.css(".base-card__full-link::attr(href)").get(default='not-found').strip()
            }

            urls.append(url_item)

            yield url_item

        self.write_to_csv(search_keywords, urls)

        # request next_url
        if (num_jobs_returned > 0 and first_job_on_page < self.numOfJobs):
            first_job_on_page = int(first_job_on_page) + 25
            next_url = self.api_url + str(first_job_on_page)
            yield scrapy.Request(url=next_url, callback=self.parse_job, meta={'first_job_on_page': first_job_on_page, 'first_keyword': first_keyword})
        else:
            first_keyword = first_keyword + 1
            if first_keyword < len(self.keywords):
                first_job_on_page = 0
                next_url = self.api_url_template.format(self.keywords[first_keyword], first_job_on_page)
                yield scrapy.Request(url=next_url, callback=self.parse_job, meta={'first_job_on_page': first_job_on_page, 'first_keyword': first_keyword})
            else:
                print('All keywords have been processed')

    def write_to_csv(self, search_keywords, urls):
        df = pd.DataFrame(urls)

        output_dir = 'data_url' 
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = os.path.join(output_dir, '{}.csv'.format(search_keywords))

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            if not os.path.exists(filename):
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(['url'])
            df.to_csv(csvfile, header=not csvfile.tell(), index=False)



    # def create_csv(self, search_keywords):
    #     output_dir = 'data_url' 
    #     if not os.path.exists(output_dir):
    #         os.makedirs(output_dir)

    #     filename = os.path.join(output_dir, '{}.csv'.format(search_keywords))  # Assuming 'title' exists in the item

    #     with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
    #         csv_writer = csv.writer(csvfile)
    #         csv_writer.writerow(['url', 'job_code', 'job_id'])