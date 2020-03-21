"""

Dennis Farmer

Factors of Academic Success
Data Cleaning, Analysis, and Visualization Project

"""
import numpy as np
import pandas as pd
import re # regex module
import datetime as dt
#import matplotlib.pyplot as plt
#import seaborn as sns

# Read survey spreadsheets

survey101 = pd.read_excel("Survey Spreadsheets/Factors of Academic Success Survey (1.01).xlsx")
survey202 = pd.read_excel("Survey Spreadsheets/Factors of Academic Success Survey (2.02).xlsx")
#survey303 = pd.read_excel("Survey Spreadsheets/Factors of Academic Success Survey (3.03).xlsx")

# Merge dataframes
surveydata = pd.merge(left=survey101, right=survey202, how="outer")
#surveydata = pd.merge(left=surveydata, right=survey303, how="outer")

# Remove already merged datasets from memory
del survey101, survey202

# Clean column names by making them all lowercase
surveydata.columns = map(str.lower, surveydata.columns)


# Drop columns that I've decided to not use in analysis
surveydata = surveydata.drop(['hobby', 'tv_laugh_track', 'perfectionist', 'large_ego', 'good_at_comedy', 'chosen_music_artists'], axis=1)

##########################################
# Basic data cleaning and transformation #
##########################################

# Convert list cells to lists
columns = ['self_improv', 'activities', 'watched_media']
surveydata[columns] = surveydata[columns].apply(lambda x: x.str.split(","))
    
### Calculate the average amount of sleep for each person

# Clean Time Values
def clean_bed_times(column, dataf=surveydata):
    if column == "go_to_bed":
        return pd.Series([dt.time(np.abs(time.hour - 12), time.minute, 0) 
                          if 6 < time.hour < 18 
                          else time 
                          for time in dataf[column]])
    
    elif column == "up_from_bed":
        return pd.Series([dt.time(np.abs(time.hour - 12), time.minute, 0) 
                          if time.hour > 18 
                          else time 
                          for time in dataf[column]])
    
surveydata["go_to_bed"], surveydata["up_from_bed"] = clean_bed_times("go_to_bed"), clean_bed_times("up_from_bed")

# Convert time values to datetime values based on the bedtime or waketime (so that the amount of sleep can be calculated)
def time_to_datetime(column, dataf=surveydata):
    # Insert date
    time_day = pd.Series(["2000/01/02 " 
                          if (column == 'up_from_bed' or (column == 'go_to_bed' and dataf[column][i].hour < 5)) 
                          else "2000/01/01 " 
                          for i in range(dataf.shape[0])]).astype(str)
    
    # Convert time values to strings
    time_time = dataf[column].astype(str)
    
    # Concat date and time and convert to datetime object    
    return (time_day + time_time).apply(lambda x: dt.datetime.strptime(x, "%Y/%m/%d %H:%M:%S"))

# Calculate and insert column into the dataset and convert timedelta to hours
surveydata.insert(21, 'avg_sleep_hours', (time_to_datetime('up_from_bed') - time_to_datetime('go_to_bed')).apply(lambda x: x.seconds / 3600))


### Mapping college majors column:
# For some reason my regex lookaheads and lookbehinds wont work, something to investigate
surveydata.insert(5, 'major_cat', surveydata.major.fillna("Undecided"))

mapping_majors = {"Undecided":r"general|no\sclue|undecided", "Medical":r"medi|pharmacy|nursing", "Music":r"music", "Business":r"account|manage|info", 
                  "Science":r"zoo|biology|physical|animal|agri|kinesi|science", "Technology":r"tech|computer(?!info)", 
                  "Engineering":r"(?<!medical)engineer|aviation", "Math":r"data|physics|math|economics",
                  "Fine Arts":r"art|picture|culinary|history|tourism|soci|child", "Trades":r"welding"}

for cat in ["Undecided", "Medical", "Music", "Business", "Science", "Technology", "Engineering", "Math", "Fine Arts", "Trades"]:
    surveydata.loc[surveydata.major_cat.str.contains(mapping_majors[cat], flags=re.IGNORECASE), 'major_cat'] = cat
    


### Compare SAT and ACT scores and keep the highest one as a converted SAT score
act_sat = {'36':1590, '35':1540, '34':1500, '33':1460, '32':1430, '31':1400, '30':1370, '29':1340, '28':1310, '27':1280, '26':1240, '25':1210, '24':1180, '23':1140, '22':1110, '21':1080, '20':1040, '19':1010, '18':970}
def act_to_sat(act):
    if np.isnan(act):
        return np.NaN
    else:
        score = str(int(act))
        if score in act_sat:
            return act_sat[score]
        else:
            return np.NaN
        
# Insert column and clean values
surveydata.insert(11, 'converted_sat', surveydata.act.apply(act_to_sat))
surveydata[['converted_sat', 'sat']] = surveydata[['converted_sat', 'sat']].fillna(0).astype(int)

# Keep highest score as converted SAT score
rows = (surveydata.sat > surveydata.converted_sat)
surveydata.loc[rows, 'converted_sat'] = surveydata.loc[rows, 'sat']


### Clean Myers-Briggs types to capitalize and place letters in correct order
def clean_myers_briggs(mbti):
    try:
        mbti = mbti.upper()
    except AttributeError:
        return np.NaN
    return re.findall(r'E|I', mbti)[0] + re.findall(r'S|N', mbti)[0] + re.findall(r'T|F', mbti)[0] + re.findall(r'P|J', mbti)[0]
    
surveydata.myers_briggs = surveydata.myers_briggs.apply(clean_myers_briggs)


### Create unique columns for elements in list columns
def expand_series_of_lists(in_series):
    """
    Turns a series of multiple answer responses into a boolean dataframe
    """
    
    unique_elements = []
    in_series = in_series.fillna("")
    clean_str = lambda x: x.strip().lower().replace(' ', '_')
    
    # Create a list of unique values throughout all cells in column
    for row in in_series:
        unique_elements.extend([clean_str(element) for element in row if clean_str(element) not in unique_elements])
        
                
    def create_bool_series(cell, unique):
        for element in cell:
            if unique == clean_str(element):
                return True
            else:
                pass
        return False
        
    out_dataf = pd.DataFrame()
    for u_element in unique_elements:
        out_dataf.insert(0, u_element, in_series.apply(lambda x: create_bool_series(x, unique=u_element)))
        
    # reverse order of columns
    return out_dataf[out_dataf.columns.tolist()[::-1]]             

for column in ['self_improv', 'activities', 'watched_media']:
    surveydata = pd.concat([surveydata, expand_series_of_lists(surveydata[column])], axis=1)

surveydata = surveydata.drop(['self_improv', 'activities', 'watched_media'], axis=1)

### rename column names to make data exploration less tedious
#colnames = surveydata.columns.tolist()

####################
mapping_columns = {'i_have_a_consistent_morning_routine':'routine', 'i_exercise_on_a_regular_basis':'exercise', 
                     'i_try_to_maintain_a_healthy_diet':'diet', 'i_try_to_limit_my_use_of_social_media':'limits_social_media', 
                     'i_participate_in_nofap':'nofap', 'i_keep_a_journal_for_things_like_time_management_|_personal_development/goals_|_and_idea/project_notes':'planner', 
                     "i_keep_a_diary_for_things_like_analyzing_the_day's_activities_|_tracking_mental_health_|_and_self_reflection.":'diary',
                     'i_drink_energy_drinks_on_a_semi-regular_basis':'energy_drinks', 'i_practice_meditation':'meditation', 'i_take_cold_showers':'cold_showers', 
                     'i_keep_a_planner_for_things_like_time_management_|_personal_development/goals_|_and_idea/project_notes':'planner2', 
                     "i_keep_a_journal/diary_for_things_like_analyzing_the_day's_activities_|_tracking_mental_health_|_and_self_reflection.":'diary2', 
                     'i_drink_coffee_on_a_semi-regular_basis?':'coffee2', 'i_drink_coffee_on_a_semi-regular_basis':'coffee', 'gaming_/_mtg_/_dnd_group':'gaming_club', 
                     'drum_corps':'drum_corps', 'physical_sport_(hockey_|_soccer_|_etc.)':'plays_sports','theater_/_drama_club':'theater',
                     'nature_hobby_(fishing_|_camping_|_etc.)':'nature_hobby','school_band_(concert_|_jazz_|_marching)':'school_band','indoor_drumline':'indoor_drumline',
                     'stem_club_(robotics_|_it_|_etc)':'stem_club','indoor_drumline_/_wgi':'indoor_drumline2','drum_corps_/_dci':'drum_corps2'}
####################

surveydata = surveydata.rename(columns=mapping_columns)
#colnames = surveydata.columns.tolist()

### Convert (Yes, No) to (True, False)
columns = ["social_awkward", "social_anxious", "show_up_early", "cluttered", "share_posts_often"]
surveydata[columns] = surveydata[columns].applymap(lambda x: x == "Yes")

### Combine duplicate columns (coffee = coffee2, etc)
# Duplicate columns have been differentiated by appending "2"
for column in ["coffee", "drum_corps", "indoor_drumline", "planner", "diary"]:
    surveydata[column] = surveydata[[column, column + "2"]].any(axis=1)
    surveydata = surveydata.drop([column + "2"], axis=1)

### Drop data points that are either rare or likely irrelevent (>50 columns is going to be impractical to work with)
#colsums = surveydata.sum() #put in jupiter notebook to demonstrate need to drop low sum boolean columns (6 = lower bound) (use thresh=6? not sure how to write that yet)
surveydata = surveydata.drop(['nofap','theater','gaming_club','stem_club','diary','flow:_the_psychology_of_optimal_experience_by_mihaly', 'mr._robot',
                              'eternal_sunshine_of_the_spotless_mind_(2004)', "man's_search_for_meaning_by_viktor_frankl", 'self-reliance_by_ralph_waldo_emerson'], axis=1)


### Dataset Differences:
# (I added and removed some survey questions as I was first starting this)
# index 26 represents the end of s101, 48 is end of s202


### Set missing values from datasets to NaN (instead of False)


### Convert first 36 big5 personality score rows to range 1-5 (from range 1-10)
def clean_big5(score):
    score = score//2
    if score == 0:
        return score + 1
    return score

columns = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
surveydata.iloc[:35][columns] = surveydata.iloc[:35][columns].applymap(clean_big5).copy()


    










    



####################
# Data Exploration #
####################

#number of clubs could lead to better grades
#what percentage of band nerds are religious?


#surveydata.to_excel("SurveyData")


    
#fig, axes = plt.subplots()


### Final Presentation Ideas:
# create web app that allows users to select statistics to calculate



