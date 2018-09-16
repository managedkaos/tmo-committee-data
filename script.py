import os
import pandas
from configparser import ConfigParser
from ftplib import FTP

def lambda_handler(event, context):
    # read the config file and assign values
    config = ConfigParser()
    config.read('config.txt')

    gsheet_url = config.get('gsheet','url')
    ftp_host   = config.get('ftp','host')
    ftp_user   = config.get('ftp','user')
    ftp_pass   = config.get('ftp','pass')
    local_dir  = config.get('local','dir')

    # check for the local directory and create it if needed
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    # change directory to the local directory
    os.chdir(local_dir)

    # remove the column bounds
    pandas.set_option('display.expand_frame_repr', False)
    # get the data or die
    p = pandas.read_csv(gsheet_url)

    # open ftp or die
    ftp = FTP(ftp_host)
    ftp.login(ftp_user, ftp_pass)

    # incoming column number and names
    # 0 'Timestamp',
    # 1 'First Name',
    # 2 'Last Name',
    # 3 'Phone Number (in xxx-xxx-xxxx format)',
    # 4 'Phone Number Type',
    # 5 'Preferred Email Address',
    # 6 'Contact Preference',
    # 7 'Target Committees (select at least one)',

    target_committees = [
        "Target 1: HBCU for Life: A Call to Action",
        "Target 2: Women's Healthcare and Wellness",
        "Target 3: Building Your Economic Legacy",
        "Target 4: The Arts!",
        "Target 5: Global Impact",
        "Signature Program: #CAP (College Admissions Process)",
    ]

    # simplify the column names
    p.rename(columns={'Phone Number (in xxx-xxx-xxxx format)':'Phone Number'}, inplace=True)
    p.rename(columns={'Target Committees (select at least one)':'Target Committees'}, inplace=True)

    # drop duplicates by email address
    p.drop_duplicates('Preferred Email Address', inplace=True)

    # print all member details, sorted by last name
    print("All members...")
    p.iloc[:, 1:9].sort_values(by=['Last Name'], ascending=True).to_csv('members.csv')
    p.iloc[:, 1:9].sort_values(by=['Last Name'], ascending=True).to_html('members.html')
    ftp.storbinary('STOR ' + 'members.html', open ('members.html', 'rb'))
    ftp.storbinary('STOR ' + 'members.csv', open ('members.csv', 'rb'))

    # print target committees with member details
    print("Target committees...")
    for committee in target_committees:
        committee_filename = ''.join(e for e in committee if e.isalnum())
        pslice = p[ p['Target Committees'].str.contains(committee, na=False) ]
        pslice.iloc[:, 1:9].sort_values(by=['Last Name'], ascending=True).to_csv(committee_filename + '.csv')
        pslice.iloc[:, 1:9].sort_values(by=['Last Name'], ascending=True).to_html(committee_filename + '.html')
        ftp.storlines('STOR ' + committee_filename + '.html', open (committee_filename + '.html', 'rb'))
        ftp.storlines('STOR ' + committee_filename + '.csv', open (committee_filename + '.csv', 'rb'))


if __name__ == '__main__':
    lambda_handler(None, 'handler')
