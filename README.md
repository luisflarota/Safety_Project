# Creating a Descriptive Web Dashboard for Safety Reporting

<div style='text-align:center'><em>"Software is the language of automation" - J. Huang (1963)</em></div>

--- 

<h2> Content </h2>

[1. Some Introduction](#s1) <br>
[2. The Problem](#s2) <br>
[3. The Solution ](#s3) <br>
[4. Building an Application](#s4) <br>
[5. Future Work Ideas](#s5) <br>
[6. Code!](#s6) <br>

----

<h2 id = "s1"> 1. Some Introduction </h2>
Talk about daily/weekly/monthly reports that retrieve data from different sources and have different formats. Why do not we reunite them and present it in an app.


----

<h2 id = "s2"> 2. The Problem </h2>
We sometimes might find daily, weekly and monthly reports that consume (and make us waste) a lot of time with repetitive tasks.

In the following case, we found a daily report that consumed at least 30 minutes per day. The source of data for this report comes from an ERP system, and the person building the report was supposed to download data from it and do some transformations based on the report format, i.e., filtering, getting pivot tables, drawing some charts, unpivoting tables and paste everything into a power point file - as shown in the flowchart below. Once this report was ready, mistakes must have been avoided, which meant a double check and more time wasted. Then, the report could be sent to the corresponding managers at the mine operation. <ins> This report should be done every single day until it is not needed (might not happen though).</ins>
![first](https://user-images.githubusercontent.com/64980133/185766564-2abfa5d5-461c-4271-baea-5bb5b4cc00bd.svg)


Furthermore, we also found that this "reporting person" was supposed to do a weekly and monthly report, both with similar format. The process to build these two were more cumbersome than the daily report - there were many gaps to fill out in an Excel file and numerical values that needed to be checked multiple times because these were sent to a corporate office (see the flowchart below). In practice, there is always a mistake done when dealing with multiple computations at a same time. <ins> To be more chaotic, if the "reporting" person was asked to share the Excel file from previous reports, that was his/her end because they will need to build it again.</ins>

![second](https://user-images.githubusercontent.com/64980133/185766591-dc504446-86c4-4ac5-8649-ac9dfcf6f52b.svg)


<ins> Then, how can we automate this process and make the life easier for this reporting person? What can make us focus on the actions brought from these indicators rathen than computing them?</ins>

----

<h2 id = "s3"> 3. The Solution </h2>

We thought about building a web dashboard so this conveys the daily, weekly, and monthly report. That way, each manager at the mine site could access this information in real-time.

<ins> For the daily</ins> , there is still a manual process - the "reporting person" should download a file for a current date. Once this is done, this should be uploaded to the web system and that would be it! There is a chance to build a task scheduler that automatically downloads it from a third party software, but this is still on development. In addition, on the side of <ins> the weekly and monthly report</ins> , the only manual process would be to feed the source data, as shown in the flowchart below.

![sol](https://user-images.githubusercontent.com/64980133/185766603-8e91f335-953e-4825-b13a-fca1d5df2fc9.svg)

The dashboard is built using the [Streamlit](https://streamlit.io/){:target="\_blank"}  framework in Python and there are two main components of this prospective app that may need to be described.

1- Uploading and updating the Excel parent file for a daily report.

For this case, a .txt file, containing the names of the files already saved in the parent file, i.e., SHEC-2020_Aug_2.csv, would help us check if the uploaded file is already in the Excel parent file. If the filename is not there, it would be merged with the Excel parent file, otherwise it will be avoided.
~~~python
# Text file path
dir_txt_file = r"...dates.txt"
# Folder path - this is where you will download your "newest"
dir_csv_files = r"..dir_of_your_files"
# Read text file
dates_in_txt = np.loadtxt(dir_text_file, dtype='str')
# Check if the "newest" file is already in the txt file. If so, names will be added to a list
csv_files_left = [csvfile for csvfile in os.listdir(dir_csv_files) if csvfile not in np.loadtxt(dir_text_file, dtype='str')]
# Merge files in the list with the parent file.
for csv_left in csv_files_left:
    pd_csv_left = pd.read_csv(dir_csv_files+csv_left)
    all_hazards = pd.concat([all_hazards, pd_csv_left], ignore_index=True, sort=False)
    file =  open(dir_text_file,'a')
    file.write(csv_left+'\n')
    file.close()
# Save the merged Excel file
all_hazards.to_csv('AllHazards.csv', index =False)
~~~

2- Fixing the process of reading data when the website is being clicked.

Streamlit offers a function decorator that bypasses this process if stated. The following is written explicitly in the application.

~~~python
@st.experimental_singleton
def read_files(new_hazards_file='a'):
    """
    Read the source data for daily, weekly and monthly reports.
    Args:
        new_hazards_file (str or dataframe): Help see if there is a new
                            hazard file. This plays with the function
                            decorator in line 25.
    Returns:
        Main (class): Instantiate a class that got multiple objects."""
    Main = back_.CargaReports(new_hazards_file)
    return Main

class CargaReports:
    """ 
    Load 3 main files for daily (03_AllHazrds), 
    weekly and monthly (the other 2)
    """
    def __init__(self, newhazard=0, file_hazards="03_AllHazards.xlsx", 
                file_incidents="01_Accidents_Fill.xlsx",
                man_hours="02_ManHoursWorked.csv"):
        ... 
        ...
~~~

--- 

<h2 id = "s4"> 4. Building an Application </h2>

This application has multiple features for a daily side:

* Download and upload new raw data.
![firstp](https://user-images.githubusercontent.com/64980133/185766622-0facfe40-752b-4123-8456-a9ffb8e563e2.png)

* View Report: Check main chart of organizational units meeting a specific KPI and its details. We can also download a power point file
corresponding to the chosen date.
![secp](https://user-images.githubusercontent.com/64980133/185766634-280c6f10-df5f-4110-aeec-579a39a9420f.png)

Downloaded power point file. This will be similar as shown in the web dashboard but it is ready to be sent to another people.
![thirdp](https://user-images.githubusercontent.com/64980133/185766641-6d639379-caeb-498a-87bb-70538e858497.png)

<br>

In addition, we have the following design for the weekly and monthly report.

For a weekly:
![fourth](https://user-images.githubusercontent.com/64980133/185766650-597be063-13b1-4850-b14d-5c6901406964.png)

For a monthly:
![fifth](https://user-images.githubusercontent.com/64980133/185766657-2cf59e5c-7239-4a7b-95f8-0294556a577b.png)


<h2 id = "s5"> 5. Future Work Ideas </h2>

- <ins>Build a task scheduler to (1) download data from the ERP system or (2) query a SQL database</ins>. We are downloading a "fictional" file to replicate this process, but it would be useful to have that process automated
- <ins>Predict accidents</ins>. We have live data from hazards reporting, man-hours worked, and previous incidents - with these variables, we can predict the likelihood of an accident ocurring in the future and even the likelihood of each type (including more variables for sure).


