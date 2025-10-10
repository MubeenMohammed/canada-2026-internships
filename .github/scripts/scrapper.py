from bs4 import BeautifulSoup   
import requests
import pandas as pd
import time
import json
import uuid
from datetime import datetime, timezone


#declaration of global variables
i=0
headersList = [
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'},
    # {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1'},
    # {'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36'},
    # {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'},
]


def prep_skills(skills_str):
    # separates the given string into list of skills
    # split on commas, strip whitespace and ignore empty items
    raw = skills_str.split(',')
    # replaces spaces (if any) with '+' in each skill for URL encoding
    skills = ["+".join(skill.strip().split()) for skill in raw if skill.strip()]

    return skills


def get_Url(skill,start,change_url=0):
    #sample url : https://in.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=python&location=Canada&locationId=&geoId=102713980&f_TPR=&f_PP=105556991&f_E=1&start=50

    # returns the url for the skill and start value - modified to scrape internships in Canada
    # include keywords in the query string and correctly place start
    # skill is expected to be URL-friendly (spaces replaced with '+') from prep_skills
    # Use Canada-wide search by setting location=Canada and removing the Montreal-specific geoId
    full_url = (
        "https://www.linkedin.com/jobs/search/"
        "?keywords={skill}&location=Canada&currentJobId=4310616687&f_E=1&f_TPR=r86400"
        "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&start={start}"
    ).format(skill=skill, start=start)

    return full_url


def get_headers():
    # returns the headers for making a request call
    global i
    headers=headersList[i%len(headersList)]
    i+=1
    return headers


def get_postings(url,headers):
    # returns the job postings for the given url
    print('calling url...',url)

    response=requests.get(url,headers=headers)
    # print("Response code: ",response.status_code)

    if(response.status_code==429):
        url=get_Url(skill,start+25)
        headers=get_headers()
        time.sleep(7)
        print('retrying url...',url)
        response=requests.get(url,headers=headers)
        # print("Response code: ",response.status_code)

    # creates a BeautifulSoup object from html content
    soup=BeautifulSoup(response.content,'html.parser')
    postings=soup.find_all('div',attrs={'class':'base-card'})

    
    return postings


def get_job_details(postings,df,start):

    if len(postings)==0:
        print('No more job postings found')
        return False
    
    print("No of Jobs found: ",len(postings))
    for post in postings:
        start+=1

        # Job Name/Role  --> h3 classname=base-search-card__title
        job_name=post.find('h3',attrs={'class':'base-search-card__title'}).text
        # print(job_name.strip())

        # Location    --> span classname=job-search-card__location
        company_name=post.find('a',attrs={'class':'hidden-nested-link'})

        # Company     --> a  classname=hidden-nested-link
        job_location=post.find('span',attrs={'class':'job-search-card__location'}).text

        # company's linkedin profile     --> a classname=hidden-nested-link
        profile_link=company_name['href']

        # posting date    --> time classname=job-search-card__listdate
        posted_date=post.find('time',attrs={'class':'job-search-card__listdate'})
        if posted_date:
            posted_date=posted_date['datetime']
        else:
            posted_date='-'
        
        applyPageUrl=post.find('a',attrs={'class':'base-card__full-link'})['href']

        df.loc[len(df.index)]={
                                'job_name': job_name.strip(), 
                                'company_name': company_name.text.strip(),
                                'location': job_location.strip(),
                                'profile_link': profile_link.strip(), 
                                'posted_date': posted_date.strip(),
                                'apply_page_link': applyPageUrl
                            }
    # if(len(postings)<25):
    #     return False
    return True


if __name__ == "__main__":
    
    # Create a dataframe to store the job postings
    df = pd.DataFrame(columns=['job_name', 
                            'company_name', 
                            'location', 
                            'profile_link', 
                            'posted_date',
                            'apply_page_link']
                            )
    
    # Takes input from user as string with comma separated values
    skills_str=input("Enter skills (e.g: c,java,python): ")
    skills=prep_skills(skills_str)
    # print(skills)

    # Maxiumum no.of jobs to scrape per skill
    stop=int(input("Enter no.of jobs to scrape per skills(can be less if there are no available postings):"))

    # No of jobs to scrape per skill
    for skill in skills:
        start=0
        
        while start<stop:
            # Get the url,headers for the skill
            url=get_Url(skill,start)
            headers=get_headers()

            # Get the job postings for the skill
            postings=get_postings(url,headers)

            # Check the flag value to  know if the job postings are empty
            # if empty then break out of the loop
            flag=get_job_details(postings,df,start)

            start+=25
            time.sleep(10)
            if flag==False or start>stop:
                break
    
    # Convert collected dataframe rows into the requested JSON array format
    def to_epoch(dt_str):
        """Convert an ISO-like datetime string to epoch seconds (int).
        If parsing fails or value is '-', return current epoch.
        """
        if not dt_str or dt_str == '-' or str(dt_str).strip() == '':
            return int(time.time())

        s = str(dt_str).strip()
        try:
            # handle Z timezone
            if s.endswith('Z'):
                s = s[:-1] + '+00:00'
            dt = datetime.fromisoformat(s)
            # ensure timezone-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except Exception:
            try:
                # try parsing common YYYY-MM-DD format
                dt = datetime.strptime(s[:10], '%Y-%m-%d')
                dt = dt.replace(tzinfo=timezone.utc)
                return int(dt.timestamp())
            except Exception:
                return int(time.time())

    output = []
    seen = set()
    for _, row in df.iterrows():
        posted_epoch = to_epoch(row.get('posted_date'))
        updated_epoch = int(time.time())

        apply_url = (row.get('apply_page_link') or '').strip()
        company_url = (row.get('profile_link') or '').strip()
        title = (row.get('job_name') or '').strip()
        company = (row.get('company_name') or '').strip()
        location = (row.get('location') or '').strip()

        # dedupe key: prefer the apply page URL; if missing, use company+title+location
        if apply_url:
            key = f"url:{apply_url}"
        else:
            key = f"ct:{company}|{title}|{location}"

        if key in seen:
            # skip duplicates
            continue
        seen.add(key)

        job_obj = {
            "date_updated": updated_epoch,
            "url": apply_url or "",
            "locations": [location] if location else [],
            "sponsorship": "Other",
            "active": True,
            "company_name": company or "",
            "title": title or "",
            "season": "Winter",
            "source": "MubeenMohammed",
            "id": uuid.uuid4().hex,
            "date_posted": posted_epoch,
            "company_url": company_url or "",
            "is_visible": True
        }
        output.append(job_obj)

    # write JSON array to file
    with open('jobs.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)