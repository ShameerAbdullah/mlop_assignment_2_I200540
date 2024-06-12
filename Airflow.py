from airflow.operators.python_operator import PythonOperator
from bs4 import BeautifulSoup
from datetime import datetime
from airflow import DAG
import subprocess
import requests
import csv
import os

def extract_data_from_sources():
    def retrieve_links_from_webpage(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [link.get('href') for link in soup.find_all('a', href=True)]
        return links

    def retrieve_articles_from_webpage(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        for article in soup.find_all('article'):
            title = article.find('h2')
            description = article.find('p')
            if title and description:
                articles.append({
                    'title': title.text.strip(),
                    'description': description.text.strip()
                })
        return articles

    def save_data_to_csv(data, filename):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Description'])
            for article in data:
                writer.writerow([article['title'], article['description']])

    # URLs for both WebsiteA and WebsiteB
    siteA_url = 'https://www.bbc.com/'
    siteB_url = 'https://www.dawn.com/'

    # Retrieve links from both WebsiteA and WebsiteB
    siteA_links = retrieve_links_from_webpage(siteA_url)
    siteB_links = retrieve_links_from_webpage(siteB_url)

    # Initialize a list to store articles data
    articles_data = []

    for index, link in enumerate(siteA_links, start=1):
        if link.startswith('https://www.websitea.com'):
            articles_data.extend(retrieve_articles_from_webpage(link))

    for index, link in enumerate(siteB_links, start=index):
        if link.startswith('https://www.websiteb.com'):
            articles_data.extend(retrieve_articles_from_webpage(link))


    # Save the extracted data to a CSV file
    save_directory = "D:/FAST/8th Semester/MLOPS/Assignments/A2/Implementation"
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    save_data_to_csv(articles_data, os.path.join(save_directory, 'data.csv'))

def transform_data():
    # Function to read data from the CSV file and perform transformation
    save_directory = "D:/FAST/8th Semester/MLOPS/Assignments/A2/Implementation"
    input_file_path = os.path.join(save_directory, 'data.csv')
    output_file_path = os.path.join(save_directory, 'new_data.csv')

    with open(input_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        new_data = []

        for row in reader:
            # Example transformation: Uppercase the titles
            row['Title'] = row['Title'].upper()
            new_data.append(row)

    # Save the transformed data to a new CSV file
    with open(output_file_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Title', 'Description']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_data)

    print("Data transformed successfully")

def load_new_data():
    save_directory = "D:/FAST/8th Semester/MLOPS/Assignments/A2/Implementation"
    transformed_file_path = os.path.join(save_directory, 'new_data.csv')

    # Initialize DVC
    subprocess.run(['dvc', 'init'], cwd=save_directory)

    # Add the transformed data file to DVC
    subprocess.run(['dvc', 'add', transformed_file_path], cwd=save_directory)

    # Add Google Drive remote
    subprocess.run(['dvc', 'remote', 'add', 'gdrive', 'gdrive://1x7Crtj4N69Myv8b30FFyKph8fy_wE6SX'], cwd=save_directory)

    # Set Google Drive remote as default
    subprocess.run(['dvc', 'remote', 'default', 'gdrive'], cwd=save_directory)

    # Push data to Google Drive
    subprocess.run(['dvc', 'push'], cwd=save_directory)

    # Add all files to the Git index
    subprocess.run(['git', 'add', '.'], cwd=save_directory)

    # Commit changes
    commit_message = "Update_data"  # You can customize the commit message as needed
    subprocess.run(['git', 'commit', '-m', commit_message], cwd=save_directory)

    # Push changes to GitHub
    subprocess.run(['git', 'push'], cwd=save_directory)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 12),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

dag = DAG(
    'extract_transform_load_dag',
    default_args=default_args,
    description='Extract and transform data',
    schedule_interval=None,
)

extracting_data = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data_from_sources,
    dag=dag,
)

transforming_data = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

loading_data = PythonOperator(
    task_id='load_new_data',
    python_callable=load_new_data,
    dag=dag,
)

# Define task dependencies
extracting_data >> transforming_data >> loading_data
