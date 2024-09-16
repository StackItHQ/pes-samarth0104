[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/AHFn7Vbn)
# Superjoin Hiring Assignment

### Welcome to Superjoin's hiring assignment! 🚀

### Objective
Build a solution that enables real-time synchronization of data between a Google Sheet and a specified database (e.g., MySQL, PostgreSQL). The solution should detect changes in the Google Sheet and update the database accordingly, and vice versa.

### Problem Statement
Many businesses use Google Sheets for collaborative data management and databases for more robust and scalable data storage. However, keeping the data synchronised between Google Sheets and databases is often a manual and error-prone process. Your task is to develop a solution that automates this synchronisation, ensuring that changes in one are reflected in the other in real-time.

### Requirements:
1. Real-time Synchronisation
  - Implement a system that detects changes in Google Sheets and updates the database accordingly.
   - Similarly, detect changes in the database and update the Google Sheet.
  2.	CRUD Operations
   - Ensure the system supports Create, Read, Update, and Delete operations for both Google Sheets and the database.
   - Maintain data consistency across both platforms.
   
### Optional Challenges (This is not mandatory):
1. Conflict Handling
- Develop a strategy to handle conflicts that may arise when changes are made simultaneously in both Google Sheets and the database.
- Provide options for conflict resolution (e.g., last write wins, user-defined rules).
    
2. Scalability: 	
- Ensure the solution can handle large datasets and high-frequency updates without performance degradation.
- Optimize for scalability and efficiency.

## Submission ⏰
The timeline for this submission is: **Next 2 days**

Some things you might want to take care of:
- Make use of git and commit your steps!
- Use good coding practices.
- Write beautiful and readable code. Well-written code is nothing less than a work of art.
- Use semantic variable naming.
- Your code should be organized well in files and folders which is easy to figure out.
- If there is something happening in your code that is not very intuitive, add some comments.
- Add to this README at the bottom explaining your approach (brownie points 😋)
- Use ChatGPT4o/o1/Github Co-pilot, anything that accelerates how you work 💪🏽. 

Make sure you finish the assignment a little earlier than this so you have time to make any final changes.

Once you're done, make sure you **record a video** showing your project working. The video should **NOT** be longer than 120 seconds. While you record the video, tell us about your biggest blocker, and how you overcame it! Don't be shy, talk us through, we'd love that.

We have a checklist at the bottom of this README file, which you should update as your progress with your assignment. It will help us evaluate your project.

- [x] My code's working just fine! 🥳
- [x] I have recorded a video showing it working and embedded it in the README ▶️
- [x] I have tested all the normal working cases 😎
- [x] I have even solved some edge cases (brownie points) 💪
- [x] I added my very planned-out approach to the problem at the end of this README 📜

## Got Questions❓
Feel free to check the discussions tab, you might get some help there. Check out that tab before reaching out to us. Also, did you know, the internet is a great place to explore? 😛

We're available at techhiring@superjoin.ai for all queries. 

All the best ✨.

## Developer's Section

*Add your video here, and your approach to the problem (optional). Leave some comments for us here if you want, we will be reading this :)*

## How To Run

1. **Create a Virtual Environment (Optional but Recommended)**:
   ```bash
   python -m venv venv
   ```
2. **Activate the Virtual Environment**:
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
3. **Install Dependencies**:
   Use `pip` to install all dependencies listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
4. **Upload The Given Sheets (Super.xlsx) to Google Drive**:
   Use the `uploadSheetToDrive.py` script to upload your Google Sheets file to Google Drive:
   ```bash
   python uploadSheetToDrive.py
   ```

5. **Run the Project**:
   Execute the batch file to start the project:
   ```bash
   .\start.bat
   ```

## Video
[https://github.com/user-attachments/assets/a725162c-7967-4629-a725-d8e138ca12a3](https://github.com/user-attachments/assets/a725162c-7967-4629-a725-d8e138ca12a3)

## Approach to the Problem:

1. **Started with OAuth and API enabling**:
   - Set up OAuth authentication with Google Sheets API.
   - Enabled necessary Google APIs for the project.

2. **Created a file to upload to Google Drive**:
   - Implemented file upload functionality to Google Drive for easier management of credentials and tokens.

3. **Selected MySQL as the database**:
   - Chose MySQL as the database to store and manage records, creating a structured relational data storage.

4. **Implemented Sheets to DB synchronization as a separate functionality**:
   - Developed a script to sync data from Google Sheets to MySQL database.
   - Handled data insertions, updates, and deletions based on changes in Google Sheets.

5. **Implemented DB to Sheets synchronization as a separate functionality**:
   - Developed a script to sync data from MySQL to Google Sheets.
   - Ensured that the data in Sheets reflects the latest information from the database.

6. **Merged both synchronization functionalities with lock acquisition**:
   - Combined both Sheets-to-DB and DB-to-Sheets synchronization processes.
   - Used a mutex lock to avoid race conditions between the two sync operations.
   - The synchronization works on a first-come, first-served basis, ensuring that only one process (either Sheets-to-DB or DB-to-Sheets) can execute at a time, preventing conflicts.

7. **Optimized the solution by syncing only changes**:
   - Implemented hashing to detect changes in data, reducing unnecessary sync operations.
   - Only updated Google Sheets or MySQL when data changes were detected.
   - I know Mutex-Lock :).

8. **Attempted dynamic schema creation for uploaded files**:
   - Tried to implement dynamic schema creation where uploading a new file would create a corresponding table in MySQL.
   - This attempt was not successful, and MongoDB would have been a better fit for this requirement.

9. **Developed a Flask frontend for easier CRUD operations**:
   - Simplified writing SQL queries by building a CRUD interface using Flask for better usability and faster operations.
   - Was a pain to use SQL queries so made it simpler.

## Extra 
1. Initially, CRUD operations were mistakenly handled through Python code, but it was later realized that these operations can be directly managed within Google Sheets.
2. The synchronization between Google Sheets and the database (both Sheets to DB and DB to Sheets) was implemented step by step and then merged.
3. An attempt was made to dynamically create tables from Google Sheets. However, this failed due to issues with primary keys and data types, leading to duplicates and all fields being set as varchar. As a result, a single Google Sheet with a manually defined schema was used.
4. Initially, periodic updates were implemented. This was later changed to an event-based system, where the solution looks for changes in real time.

