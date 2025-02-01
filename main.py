import requests
import json
from datetime import datetime, timedelta
from tkinter import *
from tkinter import font, ttk
from PIL import Image, ImageTk, ImageOps
from io import BytesIO
import threading
import base64
from supabase_py import create_client, Client

window = Tk()
window.title("My Football Profile")

SYSTEM_COLOURS = {
    "dark": {
        "bg": "#121215",
        "nav_buttons": "#17171A",
        "matches_bg": "#1C1C1F",
        "match_info": "#51C7EE",
        "font": "white",
        "button_color": "#499AE0"
    },

    "light": {
        "bg": "#E3E3E3",
        "nav_buttons": "#EAEAEA",
        "matches_bg": "#D9D9D9",
        "match_info": "#51C7EE",
        "font": "black",
        "button_color": "#499AE0"
    }
}

SYSTEM_MODE = "dark"
COMPETITION_SORTING_ORDER = {
    "UEFA Champions League": 0,
    "Premier League": 1,
    "FIFA World Cup": 2,
    "European Championship": 3,
    "Primera Division": 4,
    "Bundesliga": 5,
    "Serie A": 6,
    "Ligue 1": 7,
    "Championship": 8,
    "Primeira Liga": 9,
    "Eredivisie": 10,
    "Campeonato Brasileiro Série A": 11
}

# false by default, when user signs up or logs in then becomes true, after a sign up or log in the info is to be stored in a clientside database
# to automatically log the user in when app is opened, if not automatically signed in, this stays false so sign up/log in page appears
signed_in = False
supabase_url = "https://rdkisdvsjiutnuduzupt.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJka2lzZHZzaml1dG51ZHV6dXB0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE4MzkyMzQsImV4cCI6MjA0NzQxNTIzNH0.iPaSJ0rk35Nu_Af4oT6kiOmuV9bqpq4bPyix1ytib44"
# make connection to online database
supabase = create_client(supabase_url, supabase_key)

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

visited_stadiums = []

window_height = int(window.winfo_screenheight()*0.8)
window.geometry(f"{int(window_height*0.55)}x{window_height}")
window.config(bg=SYSTEM_COLOURS[SYSTEM_MODE]["bg"])
user_id = None
# gets admin user id, used to get default stadiums, clubs etc
admin_uid = supabase.table('tblUserInfo').select('user_id').eq('username', 'Admin').execute()['data'][0]['user_id']
print(admin_uid)

countries_list = sorted([list(i.values())[1] for i in supabase.table("tblCountry").select("*").execute()['data']])
clubs_dict = supabase.table('tblClub').select('club_id, club_name').eq('user_id', admin_uid).execute()
clubs_list = []
if clubs_dict['status_code'] == 200:
    for i in clubs_dict['data']:
        clubs_list.append([i['club_id'], i['club_name']])
stadiums_dict = supabase.table('tblStadium').select('stadium_id, stadium_name').eq('user_id', admin_uid).execute()
stadiums_list = []
if stadiums_dict['status_code'] == 200:
    for i in stadiums_dict['data']:
        stadiums_list.append([i['stadium_id'], i['stadium_name']])

def show_league_table(competition_name, data):
    print(data['standings'][competition_name])

def load_match_screen(match, status):
    match_info_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
    match_info_widgets[0].config(text=match['homeTeam']['shortName'])
    match_info_widgets[1].config(text=match['awayTeam']['shortName'])
    try:
        match_info_widgets[2].config(image=club_logos[match['homeTeam']['shortName']])
        match_info_widgets[2].image = club_logos[match['homeTeam']['shortName']]
    except KeyError:
        match_info_widgets[2].config(image=None)
        match_info_widgets[2].image = None
    try:
        match_info_widgets[3].config(image=club_logos[match['awayTeam']['shortName']])
        match_info_widgets[3].image = club_logos[match['awayTeam']['shortName']]
    except KeyError:
        match_info_widgets[3].config(image=None)
        match_info_widgets[3].image = None
    if match['score']['fullTime']['home'] is None:
        match_info_widgets[4].config(text="")
        match_info_widgets[5].config(text="")
    else:
        match_info_widgets[4].config(text=match['score']['fullTime']['home'])
        match_info_widgets[5].config(text=match['score']['fullTime']['away'])
    match_info_widgets[6].config(text=status)
    print(match["referees"])

def display_matches(data):
    # match sorting function
    def get_competition_key(match):
        competition_name = match['competition']['name']
        return (COMPETITION_SORTING_ORDER.get(competition_name, float('inf')), match['utcDate'])

    for i in matches_labels[1:]:
        i.grid_forget()
    for i in matches_labels:
        for j in i.winfo_children():
            j.config(text="")
    for i in matches_scrollable.winfo_children():
        i.grid_forget()

    if data == "None":
        matches_widgets[0][6].config(text="No Matches")
    elif data == "Internet":
        matches_widgets[0][6].config(text="No Internet")
    else:
        sorted_matches = sorted(data['matches'],  key=get_competition_key)
        # separate loop for image loading
        def load_images():
            for i, match in enumerate(sorted_matches):
                # Filter matches by the specified team
                # ADD IMAGE CACHING during running and store them locally on device
                # if home_team_filter == home_team or away_team_filter == away_team or (home_team_filter == "" and away_team_filter == ""):
                if True:
                    home_crest = Image.open(BytesIO(requests.get(match["homeTeam"]["crest"]).content)).convert("RGBA")
                    home_crest = Image.alpha_composite(Image.new("RGBA", home_crest.size, SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"]), home_crest)
                    home_crest = ImageTk.PhotoImage(home_crest.resize((30, 30), Image.Resampling.LANCZOS))
                    away_crest = Image.open(BytesIO(requests.get(match["awayTeam"]["crest"]).content)).convert("RGBA")
                    away_crest = Image.alpha_composite(Image.new("RGBA", away_crest.size, SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"]), away_crest)
                    away_crest = ImageTk.PhotoImage(away_crest.resize((30, 30), Image.Resampling.LANCZOS))
                    home_team_name = match['homeTeam']['shortName']
                    away_team_name = match['awayTeam']['shortName']

                    matches_widgets[i][0].config(image=home_crest)
                    matches_widgets[i][0].image = home_crest
                    matches_widgets[i][1].config(image=away_crest)
                    matches_widgets[i][1].image = away_crest
                    # caches images incase they are needed again
                    club_logos[home_team_name] = home_crest
                    club_logos[away_team_name] = away_crest

        # load images in background
        threading.Thread(target=load_images).start()

        # used to check when a new competition is being listed
        prev_competition = ""
        current_row = 0 # keeps track of which row to use for grid
        for i, match in enumerate(sorted_matches):
            # Filter matches by the specified team
            #if home_team_filter == home_team or away_team_filter == away_team or (home_team_filter == "" and away_team_filter == ""):
            if True:

                if prev_competition == match['competition']['name']:
                    matches_labels[i].grid(row=current_row, column=0, pady=10, sticky="nsew")
                    current_row += 1
                else:
                    Button(matches_scrollable, bg=SYSTEM_COLOURS[SYSTEM_MODE]["bg"], fg=SYSTEM_COLOURS[SYSTEM_MODE]["font"], font=("Segoe UI", 16), text=match['competition']['name'], bd=0, command=lambda: show_league_table(match['competition']['name'], data)).grid(row=current_row, column=0, pady=5, sticky="nsew")
                    current_row += 1
                    matches_labels[i].grid(row=current_row, column=0, pady=10, sticky="nsew")
                    current_row += 1

                prev_competition = match['competition']['name']
                # get data
                home_team_name = match['homeTeam']['shortName']
                away_team_name = match['awayTeam']['shortName']

                # compare user time and utc time so matches are in user's timezone
                utc_time = datetime.utcnow().hour
                user_time = datetime.now().hour
                time_difference = user_time - utc_time
                match_time = (datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=time_difference)).strftime('%H:%M')
                # work out minute and status of match
                time_elapsed = int((datetime.utcnow() -  datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ')).total_seconds() / 60)
                match_status = match['status']
                if match_status == "PAUSED":
                    time_elapsed = "HALFTIME"
                elif 55 > time_elapsed > 45:
                    time_elapsed = 45
                elif time_elapsed > 54:
                    time_elapsed -= 18
                if str(time_elapsed).isdigit():
                    time_elapsed = f"{time_elapsed}\'"
                full_time_score = match['score']['fullTime']
                half_time_score = match['score']['halfTime']

                # update widgets
                matches_widgets[i][2].config(text=home_team_name)
                matches_widgets[i][3].config(text=away_team_name)
                matches_widgets[i][4].config(text=full_time_score['home'])
                matches_widgets[i][5].config(text=full_time_score['away'])
                if full_time_score['home'] is None and match_status in ["IN_PLAY", "LIVE"]:
                    print("backup score used")
                    matches_widgets[i][4].config(text=0)
                    matches_widgets[i][5].config(text=0)
                # if match hasn't started display the time it starts, if its in progress show the minute of the match, if its done, show its done
                if match_status == "TIMED" or match_status == "SCHEDULED":
                    matches_widgets[i][6].config(text=match_time)
                elif match_status == "IN_PLAY" or match_status == "LIVE" or match_status == "PAUSED":
                    matches_widgets[i][6].config(text=time_elapsed)
                else:
                    matches_widgets[i][6].config(text=match_status)

                # assigns click function to frame and its labels
                matches_labels[i].bind("<Button-1>", lambda event, m=match, s=matches_widgets[i][6].cget("text"): load_match_screen(m, s))
                for child in matches_labels[i].winfo_children():
                    child.bind("<Button-1>", lambda event, m=match, s=matches_widgets[i][6].cget("text"): load_match_screen(m, s))

                # Print the scores
                print(time_elapsed)
                print("status = " + match_status)
                print(f"{home_team_name} vs {away_team_name}")
                print(f"Full-time: {full_time_score['home']} - {full_time_score['away']}")
                print(f"Half-time: {half_time_score['home']} - {half_time_score['away']}")
                print("-" * 30)

def get_matches(home_team_search, away_team_search):
    # Get today's date in the format YYYY-MM-DD
    today = datetime.today().strftime('%Y-%m-%d')
    tomorrow = today[:8] + f"{(int(today[-2:]) + 1):02d}"
    #today = "2024-11-02"
    #tomorrow = "2024-11-03"
    params = {
        'dateFrom': today,
        'dateTo': tomorrow,
    }
    # Define the team you want to filter by
    home_team_filter = home_team_search
    away_team_filter = away_team_search
    try:
        response = requests.get(BASE_URL, headers=API_KEY, params=params)
        data = response.json()

        if 'matches' in data:
            if len(data["matches"]) == 0:
                display_matches("None")
            else:
                display_matches(data)
        else:
            display_matches("None")
    except requests.exceptions.ConnectionError:
        display_matches("Internet")

BASE_URL = 'https://api.football-data.org/v4/matches'
API_KEY = {'X-Auth-Token': '7bde5e01717e4737a8a0df7b895ef94a'}

def get_image(image_data):
    # Decode base64 string to binary
    image_data = base64.b64decode(image_data)
    # Open the binary data as an image
    img = Image.open(BytesIO(image_data))
    return ImageTk.PhotoImage(img)

football_image = get_image("iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAMAAAC7IEhfAAADAFBMVEUAAAD///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////8HPQsIAAAA/3RSTlMAAQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyAhIiMkJSYnKCkqKywtLi8wMTIzNDU2Nzg5Ojs8PT4/QEFCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaW1xdXl9gYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1+f4CBgoOEhYaHiImKi4yNjo+QkZKTlJWWl5iZmpucnZ6foKGio6SlpqeoqaqrrK2ur7CxsrO0tba3uLm6u7y9vr/AwcLDxMXGx8jJysvMzc7P0NHS09TV1tfY2drb3N3e3+Dh4uPk5ebn6Onq6+zt7u/w8fLz9PX29/j5+vv8/f7rCNk1AAAA3ElEQVR4nM2UvRHCMAyF1aRgCEaBgoJBmICOHehYihHYASo4GirEOUFGP08XFy5QE9n59GzJtoj+yM482SzI1Vq5PmT591ZcwopKBTdBdYpWQurrpPTe7BIXA641ONjErCBU9GQrOPorXL5xvNRgUmcz4cEjqm0E7+SsghJSMZPm6TdWEQvht3HdMgybZ3Pk4GLY1API/UGG4NAKHmIyGLyJ96IgaUBUHCRJgCP1PJTO9TsDa+2uC3iwSskeKSWgf56ewyRuFKC+WfPxJ5ZgxZ7iPBo66Y55Pwt1sA8wnTuumqzqvgAAAABJRU5ErkJggg==")
profile_image = get_image("iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAADPUlEQVR4nMWYz6tNURTHv+vc55UQXj3Kj5EoElIiRTGRgUTJSJKUjAz8AfIjIzMZSMr0jf2YGAr5kZBSIilKES/y5N17PwZnbWe/671z7rnnXPdbt33uae+1PnvtH2ftLZUUYID58wLgGHAT+AhMAm1gHHgMXADWRW0bZf2VhUui5xPAG4r1E7gGLOsrZIADRoDbEUDLf+3oXdvfNaN3n4BdbmOobjjz30LgiTv83QGVp0kvm8A+t1lPJB2sASTAnQiurJreoQl8XhJNmSqADS9PVYCLIQGeArNIO22VouflIuAb/861XhSG+6jbzp2PRSEO8+SwpPmS2pJ673Eqk4Skk6Sj06oCGBofcKNV4aSs02slbTAzyFkwMwICiTde4sYsr35JhY5v83LGjuc5DI1WSJqteoa3U2uKKnQDOOollXF6sN3NkPXz+1noP69C6NVXL+sc3mB7vMh2N4DvlE7quhZIbP91UaVuAd/6c7sa0xS/Juleh69pK04r32KGzKwp6VaNgGE3+CjpfpHdomELDa9Ehquu5mDnupn99CD0bjN8K4GrHd/SXhRyx8/AKFF23rPGxsYapOnWCPDeHTWndZ+vNlkmdNA7XVtOGLLpTcD3KBplowdwrla4CDLkhduBD1FUuo0ewNm+wAWjUSSXAy/Jzh5FkfsFHIlsDVF17kXGLIreMHAceAD8KBHBJukJ8BKwMrJdbfNn6hl4N/CsS6A8fQdOA8Nut7fhJhvOBLgYOZik/AKBNNrxFvUQWO0+yh1DI7h5ZGfgZo9geaBfgB2lIEmHNQHmAHfdUJWT3EwKe+kEsNN95w832RnYgBt9hOuEHAfWxqM3E2BYref/A1wn5CtgLh6gPLit3iDcVP0PhTl52RlmBS6LAEOO9lDSRqVJan+vy6YqJMWbJT2WlJhZK6zWITNrS9o/ILggk3QmTr/CJpyYWRu4J2mL0pxtEIAh/9xgZi+ARhLBrVMaXg0ILgAmkg75f0uUZdV7/Tn3rqTPCix7fNG2EmVh3eFl3bcHZRR8r5K0wsz+Du8cZdcQdR8vy8iUreb1McxSSYsHBNWpsIJXS1K44fwk6XlHhUEpkTQh6ZEk/QHomHSuGxvmgwAAAABJRU5ErkJggg==")
setting_image = get_image("iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAEi0lEQVR4nM2Zy49URRTGv9Pd6EIXQoaYgcSwYWDGuCJBF+40EZW/QIJiImDER6LRpY+JfwFGdygmuvOxciKKj5XGRAwKGGYGfOBC1LjQhTpDd/9c3HPo6prbt2/3tIlfcnP73jqPr05VnXuqWqoJwIAm0Eze3QBMRXsq6/cpYGPyvumXaZJISfnzduA54Efgk1wmfgMfApeAF4CZKpuTINkA7gbeAv6hHwfDaULuQCazArwD3DMxcsmwHgFOZw6vAG2gA/wO3Ai0/JoCfvW2tsum+AZ43GXHH24n2ACWM1LdxFnb728keq9lbbhOSvZ7t11JsDWEY9PM2sCCpEfjXS4jqStpH3BaUkfSAX+Xypo/t71twcy6QMvfjQ5XFnBfSURydCvaUkQEH0h9DEJpY4nSqZKI5DAV0WOQXUfY+DL3Z2ZjR7IBnPOed2pGqgyhu0jNldxIewAcBr4CXgL2A3Pedl1wHauHWX/9up4iQ8wC+4CjwCngSMopMr452TOSZjNji94248/r/QqEjWUVU2JHZnNJ0s2SOmZGGr07Pfyr9NJJirqLoA5yW5F+Vv15T0Sxod6wPeJ3UzHJm97W9atO5GL4hsESu7ivVuLjSNiLId4m6bykaxIDo6DjOg1/Th2PguhcW9KsmV0Mg/slXZs4GgWRfhqSViWt+O9I4KMgUtUGSfdLkgGbVERvkwuN0uuuk3lf0suSzvr7ORVT5t5Epi46fv9D0g4B08DJZMLmH/ZBiJz24iBPwPOZ7DCkC/NjYGtq7CBweURDH7huk6IyafjVopcdFkqcV+EX4OGUmAGRsKeBVyl6XNXrcLbH9dd82pykAXe4bJW98Pc6HjXXtT6Dye8nXbFsuCOHrQA3ufyaOUav7N8C/JXppggfz5RxGWXy/tcoz5+sHeJj1B/iu5jsEB8HtiS8+ob4IeDnCiNlBE+4btUieS/TGYbLwKGU2DTF7iswapqZHzhm8GwmOwyp74+ArZGoFyXF/nWcRL2gIlGf8/eRqPdq/ET9p4pKp6+ndaNXFkmAv/0qa6uL4DAv9erBbR7FDc7+/1AszJnZhQbQNLMfVAxTfKxThSiLqhDFQpRbUSxUIS23AtHRE2Z2AWg21IvWKwmptvqj0tCgPNUPU/26MexGUNqJj+Biw0p+qSjBTdJ2Tbbkv+ikZjKbyypK/rbU2x7GBv2opMOSPpP0hYrt5qKKTdPnknZq9FWZIirzJUm3qbdSd0naLel2ScfM7ArQqr0NpcjqZ9exMvNVfZ6S73cZSoeL/k9XR8UwfKvhkauzcY95dovbvLqYyiJW6tDM2iFsZqgYgob6V3iZ49j8VCEW3y633eevFsES7NbalJAi5tbTkp5K3g1CV9KtNX0PBr3jtyWfO6sMPn57M9E7nrVB7/gt9r7fUeP4rQ7BJvAY8HU24asOMDcDvzH4APMM8ATrPcDMyDYpjm/fpqimUxxKZOII+MFMZhV4F9jLkCO3schlzzMUO7ZLwKe5TELyJPATMA/srLI5CZJlf0NsBDZHeyrr9ymKcu4qKUb8G+JfSEMMu2nWgjAAAAAASUVORK5CYII=")
# BGS
Label(window, bg=SYSTEM_COLOURS[SYSTEM_MODE]["nav_buttons"]).place(relx=0, rely=0.85, relwidth=1, relheight=0.15)

# MATCHES FRAME
matches_frame = Frame(window, bg=SYSTEM_COLOURS[SYSTEM_MODE]["bg"])
matches_frame.place(relx=0, rely=0, relwidth=1, relheight=0.85)
# PROFILE FRAME
profile_frame = Frame(window, bg=SYSTEM_COLOURS[SYSTEM_MODE]["bg"])
# SETTINGS FRAME
settings_frame = Frame(window, bg=SYSTEM_COLOURS[SYSTEM_MODE]["bg"])
Label(settings_frame, text="Settings", bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 18)).place(relx=0.3, rely=0.2, relwidth=0.4, relheight=0.1)

def open_matches():
    profile_frame.place_forget()
    settings_frame.place_forget()
    auth_frame.place_forget()
    matches_frame.place(relx=0, rely=0, relwidth=1, relheight=0.85)

def open_profile():
    matches_frame.place_forget()
    settings_frame.place_forget()
    if signed_in:
        profile_frame.place(relx=0, rely=0, relwidth=1, relheight=0.85)
        auth_frame.place_forget()
    else:
        auth_frame.place(relx=0, rely=0, relwidth=1, relheight=0.85)
        profile_frame.place_forget()

def open_settings():
    profile_frame.place_forget()
    matches_frame.place_forget()
    auth_frame.place_forget()
    settings_frame.place(relx=0, rely=0, relwidth=1, relheight=0.85)

# main buttons
nav_buttons = []
nav_buttons.append(Button(window, bg=SYSTEM_COLOURS[SYSTEM_MODE]["nav_buttons"], image=football_image, activebackground=SYSTEM_COLOURS[SYSTEM_MODE]["nav_buttons"], bd=0, command=open_matches))
nav_buttons[-1].place(relx=0, rely=0.85, relwidth=(1/3), relheight=0.15)
nav_buttons.append(Button(window, bg=SYSTEM_COLOURS[SYSTEM_MODE]["nav_buttons"], image=profile_image, activebackground=SYSTEM_COLOURS[SYSTEM_MODE]["nav_buttons"], bd=0, command=open_profile))
nav_buttons[-1].place(relx=(1/3), rely=0.85, relwidth=(1/3), relheight=0.15)
nav_buttons.append(Button(window, bg=SYSTEM_COLOURS[SYSTEM_MODE]["nav_buttons"], image=setting_image, activebackground=SYSTEM_COLOURS[SYSTEM_MODE]["nav_buttons"], bd=0, command=open_settings))
nav_buttons[-1].place(relx=(2/3), rely=0.85, relwidth=(1/3), relheight=0.15)

# AUTHENTICATION UI ----------------------------------------------------------------------------
complete_signup_widgets = []

# checks if the user's email has been cofirmed
def email_confirmed():
    print(f"Email confirmed at: {supabase.auth.user()['email_confirmed_at']}")
    if supabase.auth.user()['email_confirmed_at']:
        print("Email confirmed")
        return True
    else:
        print("Email not confirmed")
        return False

# called if it is currently none to make sure user account is fully filled out
def wait_for_email_auth(email):
    # go back to login page after email authentication
    def exit_email_auth():
        print("Exit email auth")
        complete_signup_frame.place_forget()
        for i in complete_signup_widgets:
            i.place_forget()
        complete_signup_widgets.clear()
        auth_frame.place(relx=0, rely=0, relwidth=1, relheight=0.85)
        switch_to_login()
    print("Wait for email auth")
    for i in complete_signup_widgets:
        i.place_forget()
    complete_signup_widgets.clear()

    complete_signup_widgets.append(Label(complete_signup_frame, text=f"Verify your email\nthen log in\nSent to: {email}", fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], font=("Segoe UI", 12)))
    complete_signup_widgets.append(Button(complete_signup_frame, text="Log In", fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], bg=SYSTEM_COLOURS[SYSTEM_MODE]['button_color'], font=("Segoe UI", 14), command=exit_email_auth))

    complete_signup_widgets[0].place(relx=0, rely=0, relwidth=1, relheight=0.4)
    complete_signup_widgets[1].place(relx=0.3, rely=0.6, relwidth=0.4, relheight=0.1)

def create_user_entry(user_id, first_name, last_name, country, username, club_id):
    print("Create user entry")
    # creates the user's row in the user info table and populates it
    print(f"Country: {country}")

    country_id = supabase.table('tblCountry').select('country_id').eq('countryName', country).execute() # gets user's country id

    print(f"Country response: {country_id}")

    country_id = country_id['data'][0]['country_id']

    response = supabase.table('tblUserInfo').insert({
        'user_id': user_id,
        'firstname': first_name,
        'lastname': last_name,
        'country_id': country_id,
        'username': username,
        'favourite_team_id': club_id
    }).execute()

    return response

def signup_user(email, password, password2):
    if len(email) == 0:
        sign_up_widgets[9].config(text="Enter Email")
        return
    elif len(email) > 30:
        sign_up_widgets[9].config(text="Email too long")
        return
    elif not '@' in email:
        sign_up_widgets[9].config(text="Incorrect Email format")
        return
    elif len(password) < 8:
        sign_up_widgets[9].config(text="Password too short")
        return
    elif len(password) > 30:
        sign_up_widgets[9].config(text="Password too long")
        return
    elif not any(char.isupper() for char in password):
        sign_up_widgets[9].config(text="Password must include uppercase")
        return
    elif not any(char.islower() for char in password):
        sign_up_widgets[9].config(text="Password must include lowercase")
        return
    elif not any(char.isdigit() for char in password):
        sign_up_widgets[9].config(text="Password must include number")
        return
    elif not password == password2:
        sign_up_widgets[9].config(text="Passwords do not match")
        return
    # Sign up the user in the database
    response = supabase.auth.sign_up(
        email=email,
        password=password
    )

    print(f"sign up user: {response}")

    if not response['status_code'] in [200, 201]:
        if response.get('error'):
            print("Signup Error:", response["error"]["message"])
        elif response.get('msg'):
            print(response['msg'])
    else:
        print("User signed up successfully")
        # save user metadata
        user_id = response['id']
        complete_signup_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        auth_frame.place_forget()
        # tells user to confirm email
        wait_for_email_auth(email)

    sign_up_widgets[2].delete(0, END)
    sign_up_widgets[4].delete(0, END)
    sign_up_widgets[8].delete(0, END)

def clear_signup_widgets():
    for item in sign_up_widgets:
        if isinstance(item, list):
            # If the item is a list, recurse through its elements
            for sub_item in item:
                if hasattr(sub_item, "place_forget"):
                    sub_item.place_forget()
        else:
            # If the item is not a list, call place_forget directly
            if hasattr(item, "place_forget"):
                item.place_forget()

    complete_signup_widgets.clear()

def login_user(email, password):
    global signed_in, user_id
    def create_signup_widgets():
        def complete_signup():
            global signed_in
            # gets inputted values
            username = complete_signup_widgets[0][2].get().strip()
            fav_club = complete_signup_widgets[0][4].get()
            first_name = complete_signup_widgets[0][7].get().strip().capitalize()
            last_name = complete_signup_widgets[0][9].get().strip().capitalize()
            country = complete_signup_widgets[0][11].get()
            for i in clubs_list:
                if i[1] == fav_club:
                    club_id = i[0]
            # check if data is valid
            if len(username) < 3:
                complete_signup_widgets[0][12].config(text="Username too short")
                return
            elif len(first_name) < 2:
                complete_signup_widgets[0][12].config(text="Firstname too short")
                return
            elif len(last_name) < 2:
                complete_signup_widgets[0][12].config(text="Lastname too short")
                return
            elif len(fav_club) == 0:
                complete_signup_widgets[0][12].config(text="Choose a club")
                return
            elif len(country) == 0:
                complete_signup_widgets[0][12].config(text="Choose a country")
                return

            # inserts data into database
            entry_response = create_user_entry(user_id, first_name, last_name, country, username, club_id)
            print(entry_response)

            # checks insert succeeded
            if not entry_response['status_code'] in [200, 201]:
                print("Insert failed")
                complete_signup_widgets[0][5].config(bg="red", text="Error, retry later")
                return

            user_signed_in()
            complete_signup_frame.place_forget()
            account_labels[0].config(text=username)
            account_labels[1].config(text=fav_club)
            complete_signup_widgets[0][12].config(text="")
            profile_frame.place(relx=0, rely=0, relwidth=1, relheight=0.85)

        clear_signup_widgets()
        clubs_choices = [i[1] for i in clubs_list]
        complete_signup_widgets.append([Label(complete_signup_frame, text="Complete Sign Up", fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], bg=SYSTEM_COLOURS[SYSTEM_MODE]['nav_buttons'], font=("Segoe UI", 15)),
                                        Label(complete_signup_frame, text="Username", fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], font=("Segoe UI", 12)),
                                        Entry(complete_signup_frame, fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], font=("Segoe UI", 15)),
                                        Label(complete_signup_frame, text="Favourite Club", fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], font=("Segoe UI", 12)),
                                        ttk.Combobox(complete_signup_frame, values=clubs_choices, state="readonly", style="Custom.TCombobox"),
                                        Button(complete_signup_frame, text="Confirm", bg=SYSTEM_COLOURS[SYSTEM_MODE]['button_color'], fg="white", font=("Segoe UI", 12)),
                                        Label(complete_signup_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="First Name"),
                                        Entry(complete_signup_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 15)),
                                        Label(complete_signup_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="Last Name"),
                                        Entry(complete_signup_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 15)),
                                        Label(complete_signup_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="Country"),
                                        ttk.Combobox(complete_signup_frame, values=countries_list, state="readonly", style="Custom.TCombobox"),
                                        Label(complete_signup_frame, fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], font=("Segoe UI", 12, "bold"))])

        complete_signup_widgets[0][5].config(command=complete_signup)

        complete_signup_widgets[0][0].place(relx=0, rely=0, relwidth=1, relheight=0.15)
        complete_signup_widgets[0][6].place(relx=0, rely=0.2, relwidth=0.3, relheight=0.06)
        complete_signup_widgets[0][7].place(relx=0.3, rely=0.2, relwidth=0.6, relheight=0.06)
        complete_signup_widgets[0][8].place(relx=0, rely=0.32, relwidth=0.3, relheight=0.06)
        complete_signup_widgets[0][9].place(relx=0.3, rely=0.32, relwidth=0.6, relheight=0.06)
        complete_signup_widgets[0][1].place(relx=0, rely=0.44, relwidth=0.3, relheight=0.06)
        complete_signup_widgets[0][2].place(relx=0.3, rely=0.44, relwidth=0.6, relheight=0.06)
        complete_signup_widgets[0][3].place(relx=0, rely=0.56, relwidth=0.3, relheight=0.06)
        complete_signup_widgets[0][4].place(relx=0.3, rely=0.56, relwidth=0.6, relheight=0.06)
        complete_signup_widgets[0][10].place(relx=0, rely=0.68, relwidth=0.3, relheight=0.06)
        complete_signup_widgets[0][11].place(relx=0.3, rely=0.68, relwidth=0.6, relheight=0.06)
        complete_signup_widgets[0][12].place(relx=0, rely=0.74, relwidth=1, relheight=0.06)
        complete_signup_widgets[0][5].place(relx=0.3, rely=0.8, relwidth=0.4, relheight=0.1)

    if len(email) == 0:
        sign_up_widgets[9].config(text="Enter email")
        return
    elif len(password) == 0:
        sign_up_widgets[9].config(text="Enter password")
        return
    # Log in the user
    response = supabase.auth.sign_in(email=email,
        password=password)

    print(f"login user: {response}")

    error_message = None
    # if there is an error
    if 'error_code' in response:
        print("Error code")
        error_message = response['msg']
        sign_up_widgets[9].config(text=response['msg'])
    else:
        # succesfully logged in
        if response:
            print("Logged in")
            # clears log in widgets
            sign_up_widgets[6].config(bg=SYSTEM_COLOURS[SYSTEM_MODE]['button_color'], text="Log In")
            sign_up_widgets[9].config(text="")
            sign_up_widgets[2].delete(0, END)
            sign_up_widgets[4].delete(0, END)

            user_id = response['user']['id']
            access_token = response['access_token']
            refresh_token = response['refresh_token']
            token_expiry_time = response['expires_in']
            print(supabase.auth.session())
            print("Logged in user:", user_id)

            auth_frame.place_forget()
            complete_signup_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            create_signup_widgets()
            open_objectives()
            update_visited_stadiums()

            # adds users custom clubs to the clubs list
            if user_id != admin_uid:
                clubs_dict = supabase.table('tblClub').select('club_id, club_name').eq('user_id', user_id).execute()
                if clubs_dict['status_code'] == 200:
                    for i in clubs_dict['data']:
                        clubs_list.append([i['club_id'], i['club_name']])

            print(clubs_list)

            print(supabase.table('tblUserInfo').select('*').eq('user_id', user_id).execute())
            # checks if user has inputted a username, if they have then their account must be fully created so can proceed, otherwise sent to complete sign up screen
            user_data = supabase.table('tblUserInfo').select('*').eq('user_id', user_id).execute()['data']
            if user_data:
                user_data = user_data[0]
                user_signed_in()
                complete_signup_frame.place_forget()
                account_labels[0].config(text=user_data['username'])
                if user_data['favourite_team_id'] is not None:
                    club_name = supabase.table('tblClub').select('club_name').eq('club_id', str(user_data['favourite_team_id'])).execute()['data'][0]
                    account_labels[1].config(text=club_name['club_name'])
                profile_frame.place(relx=0, rely=0, relwidth=1, relheight=0.85)

        else:
            error_message = "Unexpected error"

    if error_message:
        print(f"Error: {error_message}")

style = ttk.Style()
style.theme_use("default")  # Ensure default theme is used (just in case)

style.configure(
    "Custom.TCombobox",
    fieldbackground=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"],  # Background color of entry field
    background=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"],       # Background color of dropdown
    foreground=SYSTEM_COLOURS[SYSTEM_MODE]["font"],              # Text color inside the field
    selectbackground=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"],  # Background color of selected item
    selectforeground=SYSTEM_COLOURS[SYSTEM_MODE]["font"],        # Text color of selected item
    arrowsize=30  # This can be used to control the arrow size, optional
)

# page where email is verified, username is input and favourite team is selected
complete_signup_frame = Frame(window, bg=SYSTEM_COLOURS[SYSTEM_MODE]["bg"])
# where user logs in and signs up
auth_frame = Frame(window, bg=SYSTEM_COLOURS[SYSTEM_MODE]["bg"])

# all widgets specific to signing up
sign_up_widgets = []

def switch_to_sign_up():
    sign_up_widgets[5].config(text="Login Instead", command=switch_to_login)
    sign_up_widgets[0].config(text="Sign Up")
    sign_up_widgets[6].config(text="Sign Up", command=lambda: signup_user(sign_up_widgets[2].get(), sign_up_widgets[4].get(), sign_up_widgets[8].get()))
    sign_up_widgets[9].config(text="")
    sign_up_widgets[0].place(relx=0.1, rely=0, relwidth=0.8, relheight=0.1)  # Title
    sign_up_widgets[1].place(relx=0.1, rely=0.2, relwidth=0.2, relheight=0.08)  # Email label
    sign_up_widgets[2].place(relx=0.3, rely=0.2, relwidth=0.6, relheight=0.08)  # Email entry
    sign_up_widgets[3].place(relx=0.1, rely=0.32, relwidth=0.2, relheight=0.08)  # Password label
    sign_up_widgets[4].place(relx=0.3, rely=0.32, relwidth=0.6, relheight=0.08)  # Password entry
    sign_up_widgets[5].place(relx=0.35, rely=0.12, relwidth=0.3, relheight=0.05)  # switch login/ sign up button
    sign_up_widgets[6].place(relx=0.35, rely=0.9, relwidth=0.3, relheight=0.06)  # login/ sign up button
    sign_up_widgets[7].place(relx=0.1, rely=0.44, relwidth=0.2, relheight=0.08)  # Password confirmation label
    sign_up_widgets[8].place(relx=0.3, rely=0.44, relwidth=0.6, relheight=0.08)  # Password confirmation entry
    sign_up_widgets[9].place(relx=0, rely=0.7, relwidth=1, relheight=0.18) # error display label

def switch_to_login():
    sign_up_widgets[5].config(text="Sign Up Instead", command=switch_to_sign_up)
    sign_up_widgets[0].config(text="Login")
    sign_up_widgets[6].config(text="Login", command=lambda: login_user(sign_up_widgets[2].get(), sign_up_widgets[4].get()))
    sign_up_widgets[9].config(text="")
    sign_up_widgets[7].place_forget()
    sign_up_widgets[8].place_forget()

# Add widgets to the list
sign_up_widgets.append(Label(auth_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 20, "bold"), text="Sign Up"))
sign_up_widgets.append(Label(auth_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="Email"))
sign_up_widgets.append(Entry(auth_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 15)))
sign_up_widgets.append(Label(auth_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="Password"))
sign_up_widgets.append(Entry(auth_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 15), show="•"))
sign_up_widgets.append(Button(auth_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['nav_buttons'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="Login Instead", bd=0, activebackground=SYSTEM_COLOURS[SYSTEM_MODE]['nav_buttons'], activeforeground=SYSTEM_COLOURS[SYSTEM_MODE]['font'], command=switch_to_login))
sign_up_widgets.append(Button(auth_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['button_color'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="Sign Up", bd=0, activebackground=SYSTEM_COLOURS[SYSTEM_MODE]['nav_buttons'], activeforeground=SYSTEM_COLOURS[SYSTEM_MODE]['font']))
sign_up_widgets.append(Label(auth_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="Confirm"))
sign_up_widgets.append(Entry(auth_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 15), show="•"))
sign_up_widgets.append(Label(auth_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12, "bold")))

switch_to_sign_up()
switch_to_login()
# ----------------------------------------------------------------------------------------------

selected_matches_date = Label(matches_frame, text="Today", fg=SYSTEM_COLOURS[SYSTEM_MODE]["font"], bg=SYSTEM_COLOURS[SYSTEM_MODE]["nav_buttons"], font=("Segoe UI", 15, "bold"))
selected_matches_date.place(relx=0.4, rely=0, relwidth=0.2, relheight=0.08)

# Create a canvas and a scrollbar to make the matches scrollable
canvas = Canvas(matches_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]["bg"], highlightthickness=0)
canvas.place(relx=0.1, rely=0.1, relwidth=0.8, relheight=0.9)
scrollbar = Scrollbar(matches_frame, orient="vertical", command=canvas.yview, bg=SYSTEM_COLOURS[SYSTEM_MODE]["nav_buttons"], troughcolor=SYSTEM_COLOURS[SYSTEM_MODE]["nav_buttons"])
scrollbar.place(relx=0.9, rely=0.1, relheight=0.9)

canvas.configure(yscrollcommand=scrollbar.set)

# Frame inside the canvas
matches_scrollable = Frame(canvas, bg=SYSTEM_COLOURS[SYSTEM_MODE]["bg"])

# Embed the frame into the canvas
window_frame = canvas.create_window((0, 0), window=matches_scrollable, anchor="nw")

# Update the canvas width and height dynamically based on window size
def update_canvas_size(event):
    # Adjust the frame width to match the canvas
    canvas.itemconfig(window_frame, width=event.width)
    # Set the scrollable region to the full height of the frame content
    canvas.configure(scrollregion=canvas.bbox("all"))

# Bind the <Configure> event to dynamically resize the embedded frame when the canvas changes size
canvas.bind("<Configure>", update_canvas_size)

# Update the scroll region to encompass the frame content dynamically
matches_scrollable.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

# Configure mousewheel scrolling (with platform-specific adjustment)
def _on_mousewheel(event):
    # Adjust scrolling for Windows/macOS, only scrolls is user is on matches screen
    if matches_frame.winfo_ismapped() and not match_info_frame.winfo_ismapped():
        if window.tk.call('tk', 'windowingsystem') == 'win32':
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            canvas.yview_scroll(int(-1 * event.delta), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows, macOS scroll
canvas.bind_all("<Button-4>", _on_mousewheel)    # Linux scroll up
canvas.bind_all("<Button-5>", _on_mousewheel)    # Linux scroll down

def user_signed_in():
    global signed_in
    signed_in = True
    settings_widgets[0].place(relx=0.1, rely=0.65, relwidth=0.8, relheight=0.1)
    settings_widgets[1].place(relx=0.1, rely=0.8, relwidth=0.8, relheight=0.1)

def user_signed_out():
    global signed_in
    signed_in = False
    settings_widgets[0].place_forget()
    settings_widgets[1].place_forget()
    supabase.auth.sign_out()
    switch_to_sign_up()
    switch_to_login()

# widget creation for matches menu
matches_labels = []
matches_widgets = []
# store club logos so they don't need to be loaded a second time
club_logos = {}

back_arrow = ImageTk.PhotoImage(Image.open('back arrow.png').resize((30, 30), Image.Resampling.LANCZOS))

# MATCH INFO FRAME --------------------------------------------------------
# 0, 1 = home, away name, 2, 3 = home, away logo, 5, 6 = home, away score, 7 = match status
match_info_widgets = []
match_info_frame = Frame(matches_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]["bg"])
Label(match_info_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"]).place(relx=0, rely=0, relwidth=1, relheight=0.2)
match_info_widgets.append(Label(match_info_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], fg=SYSTEM_COLOURS[SYSTEM_MODE]["font"], font=("Segoe UI", 10)))
match_info_widgets[-1].place(relx=0, rely=0, relwidth=0.25, relheight=0.2)
match_info_widgets.append(Label(match_info_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], fg=SYSTEM_COLOURS[SYSTEM_MODE]["font"], font=("Segoe UI", 10)))
match_info_widgets[-1].place(relx=0.75, rely=0, relwidth=0.25, relheight=0.2)
match_info_widgets.append(Label(match_info_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"]))
match_info_widgets[-1].place(relx=0.25, rely=0, relwidth=0.15, relheight=0.2)
match_info_widgets.append(Label(match_info_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"]))
match_info_widgets[-1].place(relx=0.6, rely=0, relwidth=0.15, relheight=0.2)
match_info_widgets.append(Label(match_info_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], fg=SYSTEM_COLOURS[SYSTEM_MODE]["font"], font=("Segoe UI", 12)))
match_info_widgets[-1].place(relx=0.4, rely=0, relwidth=0.1, relheight=0.2)
match_info_widgets.append(Label(match_info_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], fg=SYSTEM_COLOURS[SYSTEM_MODE]["font"], font=("Segoe UI", 12)))
match_info_widgets[-1].place(relx=0.5, rely=0, relwidth=0.1, relheight=0.2)
match_info_widgets.append(Label(match_info_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], fg=SYSTEM_COLOURS[SYSTEM_MODE]["match_info"], font=("Segoe UI", 12)))
match_info_widgets[-1].place(relx=0.35, rely=0.14, relwidth=0.3, relheight=0.06)
Button(match_info_frame,bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], image=back_arrow, command=lambda: match_info_frame.place_forget(), bd=0, activebackground=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], activeforeground=SYSTEM_COLOURS[SYSTEM_MODE]["font"]).place(relx=0, rely=0, relwidth=0.1, relheight=0.07)
# -------------------------------------------------------------------------

# NEW STADIUM VISIT FRAME --------------------------------------------------

def sort_stadiums_alphabetically():
    global visited_stadiums
    if len(visited_stadiums) == 0:
        return
    visited_stadiums = sorted(visited_stadiums, key=lambda x: x['stadium_id']['stadium_name'])
    for i, data in enumerate(visited_stadiums):
        print(data)
        visit_date = data['visit_date']
        stadium_name = data['stadium_id']['stadium_name']
        stadium_labels[i].config(text=f'{stadium_name} on {visit_date}')
        if not stadium_labels[i].winfo_ismapped():
            stadium_labels[i].grid(row=i, column=0, sticky='w')

def sort_stadiums_by_date():
    global visited_stadiums
    if len(visited_stadiums) == 0:
        return
    visited_stadiums = sorted(visited_stadiums, key=lambda x: x['visit_date'], reverse=True)
    for i, data in enumerate(visited_stadiums):
        print(data)
        visit_date = data['visit_date']
        stadium_name = data['stadium_id']['stadium_name']
        stadium_labels[i].config(text=f'{stadium_name} on {visit_date}')
        if not stadium_labels[i].winfo_ismapped():
            stadium_labels[i].grid(row=i, column=0, sticky='w')

def update_visited_stadiums():
    global visited_stadiums
    response = supabase.table("tblUserStadium").select("visit_date, stadium_id(stadium_name)").eq('user_id', user_id).execute()
    print(response)
    if response['status_code'] in [200, 201]:
        visited_stadiums = sorted(response['data'], key=lambda x: x['stadium_id']['stadium_name'])
        num_stadiums = len(visited_stadiums)
        # if no stadiums to place, no labels needed and no updating of labels needed
        if num_stadiums == 0:
            for i in stadium_labels:
                i.place_forget()
                i.remove()
                return
        difference = len(stadium_labels) - num_stadiums
        # update amount of labels to match amount of stadiums to display
        if difference < 0:
            difference *= -1
            for i in range(difference):
                stadium_labels.append(Label(stadiums_display_frame, fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 10), bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg']))
        elif difference > 0:
            for i in range(difference):
                stadium_labels.pop().destroy()

        print(visited_stadiums)

        for i, data in enumerate(visited_stadiums):
            print(data)
            visit_date = data['visit_date']
            stadium_name = data['stadium_id']['stadium_name']
            stadium_labels[i].config(text=f'{stadium_name} on {visit_date}')
            if not stadium_labels[i].winfo_ismapped():
                stadium_labels[i].grid(row=i, column=0, sticky='w')

        stadiums_display_frame.update_idletasks()
        stadiums_canvas.config(scrollregion=stadiums_canvas.bbox("all"))
        for i in stadiums_display_frame.winfo_children():
            i.bind("<MouseWheel>", on_stadium_mouse_wheel)

stadium_labels = []

def open_new_stadium_visit():
    current_date = datetime.today().strftime('%#d-%#m-%Y').split('-')
    stadium_visit_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
    stadium_visit_widgets[1].set(current_date[0])
    stadium_visit_widgets[2].set(months[int(current_date[1]) - 1])
    stadium_visit_widgets[3].config(text=current_date[2])
    stadium_visit_widgets[4].config(text='')

def close_new_stadium_visit():
    stadium_visit_frame.place_forget()

def add_stadium_visit():
    if stadium_visit_widgets[0].get() == '':
        stadium_visit_widgets[4].config(text="Select a Stadium")
        return
    elif stadium_visit_widgets[1].get() == '':
        stadium_visit_widgets[4].config(text="Select a Day")
        return
    elif stadium_visit_widgets[2].get() == '':
        stadium_visit_widgets[4].config(text="Select a Month")
        return
    elif (stadium_visit_widgets[2].get() in ['April', 'June', 'September', 'November'] and stadium_visit_widgets[1].get() == '31') or stadium_visit_widgets[2].get() == 'February' and stadium_visit_widgets[1].get() in ['30', '31']:
        stadium_visit_widgets[4].config(text="Invalid Date")
        return

    visit_year = stadium_visit_widgets[3].cget('text')
    visit_month = f'{months.index(stadium_visit_widgets[2].get()) + 1:02}'
    visit_day = f'{int(stadium_visit_widgets[1].get()):02}'
    visit_date = f'{visit_year}-{visit_month}-{visit_day}'
    stadium_id = 0
    for i in stadiums_list:
        if i[1] == stadium_visit_widgets[0].get():
            stadium_id = i[0]

    response = supabase.table('tblUserStadium').insert({'visit_date':visit_date, 'user_id':user_id, 'stadium_id':stadium_id}).execute()
    print(response)

    if not response['status_code'] in [200, 201]:
        stadium_visit_widgets[4].config(text=response['data']['message'])
        return

    update_visited_stadiums()
    close_new_stadium_visit()

def add_year():
    current_year = int(stadium_visit_widgets[3].cget('text'))
    if current_year < 9999:
        stadium_visit_widgets[3].config(text=current_year + 1)

def sub_year():
    current_year = int(stadium_visit_widgets[3].cget('text'))
    if current_year > 1:
        stadium_visit_widgets[3].config(text=current_year - 1)

stadium_visit_frame = Frame(window, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'])
Button(stadium_visit_frame, image=back_arrow, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], bd=0, activebackground=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], command=close_new_stadium_visit).place(relx=0, rely=0, relwidth=0.1, relheight=0.1)
Label(stadium_visit_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], text='Stadium', font=("Segoe UI", 14)).place(relx=0, rely=0.25, relwidth=0.25, relheight=0.08)
Label(stadium_visit_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], text='Visit Date', font=("Segoe UI", 14)).place(relx=0, rely=0.45, relwidth=0.25, relheight=0.08)
Button(stadium_visit_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['button_color'], fg='white', font=("Segoe UI", 15), text="Add", bd=0, command=add_stadium_visit).place(relx=0.35, rely=0.8, relwidth=0.3, relheight=0.1)
Button(stadium_visit_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg='white', font=("Segoe UI", 15), text="+", bd=0, command=add_year).place(relx=0.6, rely=0.41, relwidth=0.2, relheight=0.04)
Button(stadium_visit_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg='white', font=("Segoe UI", 15), text="-", bd=0, command=sub_year).place(relx=0.6, rely=0.53, relwidth=0.2, relheight=0.04)
stadium_visit_widgets = []
stadium_visit_widgets.append(ttk.Combobox(stadium_visit_frame, values=sorted([i[1] for i in stadiums_list]), state="readonly"))
stadium_visit_widgets.append(ttk.Combobox(stadium_visit_frame, values=[str(i) for i in range(1, 32)], state="readonly"))
stadium_visit_widgets.append(ttk.Combobox(stadium_visit_frame, values=months, state="readonly"))
stadium_visit_widgets.append(Label(stadium_visit_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 14)))
stadium_visit_widgets.append(Label(stadium_visit_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 11, 'bold')))
stadium_visit_widgets[0].place(relx=0.25, rely=0.25, relwidth=0.6, relheight=0.08)
stadium_visit_widgets[1].place(relx=0.25, rely=0.45, relwidth=0.1, relheight=0.08)
stadium_visit_widgets[2].place(relx=0.375, rely=0.45, relwidth=0.2, relheight=0.08)
stadium_visit_widgets[3].place(relx=0.6, rely=0.45, relwidth=0.2, relheight=0.08)
stadium_visit_widgets[4].place(relx=0, rely=0.65, relwidth=1, relheight=0.1)
# --------------------------------------------------------------------------

# ACCOUNT FRAME --------------------------------------------------------------
def open_objectives():
    account_labels[2].place(relx=0.2/3, rely=0.995, relwidth=0.6/3, relheight=0.003)
    objectives_frame.place(relx=0, rely=0.25, relwidth=1, relheight=0.65)
    account_labels[3].place_forget()
    account_labels[4].place_forget()
    stadiums_frame.place_forget()
    match_history_frame.place_forget()

def open_match_history():
    account_labels[3].place(relx=1.2 / 3, rely=0.995, relwidth=0.6 / 3, relheight=0.003)
    match_history_frame.place(relx=0, rely=0.25, relwidth=1, relheight=0.65)
    account_labels[2].place_forget()
    account_labels[4].place_forget()
    stadiums_frame.place_forget()
    objectives_frame.place_forget()

def open_stadiums():
    account_labels[4].place(relx=2.2 / 3, rely=0.995, relwidth=0.6 / 3, relheight=0.003)
    stadiums_frame.place(relx=0, rely=0.25, relwidth=1, relheight=0.65)
    account_labels[2].place_forget()
    account_labels[3].place_forget()
    objectives_frame.place_forget()
    match_history_frame.place_forget()

account_img = ImageTk.PhotoImage(Image.open('profile.png').resize((100, 100), Image.Resampling.LANCZOS))
add_stadium_img = ImageTk.PhotoImage(Image.open('AddStadium.png').resize((80, 80), Image.Resampling.LANCZOS))

objectives_frame = Frame(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'])
match_history_frame = Frame(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'])
stadiums_frame = Frame(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'])

Button(stadiums_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], image=add_stadium_img, bd=0, activebackground=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], command=open_new_stadium_visit).place(relx=0.77, rely=0.77, relwidth=0.23, relheight=0.23)
stadiums_canvas = Canvas(stadiums_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'], bd=0, highlightthickness=0)
stadiums_canvas.place(relx=0, rely=0, relwidth=0.77, relheight=1)
stadiums_display_frame = Frame(stadiums_canvas, bg=SYSTEM_COLOURS[SYSTEM_MODE]['bg'])
stadiums_display_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
stadiums_scrollbar = Scrollbar(stadiums_frame, orient="vertical", command=stadiums_canvas.yview)

Button(stadiums_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['button_color'], fg='white', text="Sort A-Z", command=sort_stadiums_alphabetically).place(relx=0.8, rely=0.25, relwidth=0.2, relheight=0.15)
Button(stadiums_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['button_color'], fg='white', text="Sort by Date", command=sort_stadiums_by_date).place(relx=0.8, rely=0.5, relwidth=0.2, relheight=0.15)

# configure for scrolling
stadiums_canvas.create_window((0, 0), window=stadiums_display_frame, anchor="nw")
stadiums_canvas.configure(yscrollcommand=stadiums_scrollbar.set)

stadiums_scrollbar.pack(side="right", fill="y")

def on_stadium_mouse_wheel(event):
    if stadiums_frame.winfo_ismapped():
        # Use the delta value from the event to scroll
        stadiums_canvas.yview_scroll(-1 * (event.delta // 120), "units")

# Bind the scroll wheel to the canvas
stadiums_canvas.bind("<MouseWheel>", on_stadium_mouse_wheel)
stadiums_display_frame.bind("<MouseWheel>", on_stadium_mouse_wheel)

account_labels = []
# 0 = username, 1 = favourite team, 2 = objectives highlight, 3 = matches highlight, 4 = stadiums highlight

# these widgets are not added to the list as they are static
Label(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg']).place(relx=0, rely=0, relwidth=1, relheight=0.25)
Label(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], image=account_img).place(relx=0, rely=0.05, relwidth=0.35, relheight=0.2)
Label(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12, 'bold'), text="Favourite Team").place(relx=0.3, rely=0, relwidth=0.7, relheight=0.04)
Label(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12, 'bold'), text="Fan Type").place(relx=0.3, rely=0.1, relwidth=0.7, relheight=0.04)
Button(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="Objectives", bd=0, activeforeground=SYSTEM_COLOURS[SYSTEM_MODE]['font'], activebackground=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], command=open_objectives).place(relx=0, rely=0.9, relwidth=1/3, relheight=0.1)
Button(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="Match History", bd=0, activeforeground=SYSTEM_COLOURS[SYSTEM_MODE]['font'], activebackground=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], command=open_match_history).place(relx=1/3, rely=0.9, relwidth=1/3, relheight=0.1)
Button(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 12), text="Stadiums", bd=0, activeforeground=SYSTEM_COLOURS[SYSTEM_MODE]['font'], activebackground=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], command=open_stadiums).place(relx=2/3, rely=0.9, relwidth=1/3, relheight=0.1)

# these widgets are added to the list as they change
account_labels.append(Label(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], font=("Segoe UI", 12), fg=SYSTEM_COLOURS[SYSTEM_MODE]['font']))
account_labels.append(Label(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], font=("Segoe UI", 12), fg=SYSTEM_COLOURS[SYSTEM_MODE]['font']))
account_labels.append(Label(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['match_info']))
account_labels.append(Label(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['match_info']))
account_labels.append(Label(profile_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['match_info']))

account_labels[0].place(relx=0, rely=0, relwidth=0.35, relheight=0.05)
account_labels[1].place(relx=0.3, rely=0.04, relwidth=0.7, relheight=0.05)
# ------------------------------------------------------------------------------

# SETTINGS FRAME ---------------------------------------------------------------
settings_widgets = []
Button(settings_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 16), text="Session", bd=0, command=lambda: print(f'Session:  {supabase.auth.session()}')).place(relx=0.1, rely=0.5, relwidth=0.8, relheight=0.1)
settings_widgets.append(Button(settings_frame, bg=SYSTEM_COLOURS[SYSTEM_MODE]['matches_bg'], fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 16), text='Log Out', bd=0, command=user_signed_out))
settings_widgets.append(Button(settings_frame, bg='red', fg=SYSTEM_COLOURS[SYSTEM_MODE]['font'], font=("Segoe UI", 16), text='Delete Account', bd=0))
# ------------------------------------------------------------------------------

matches_scrollable.columnconfigure(0, weight=1)  # Make column 0 stretchable

for i in range(80):
    # Create a label container for each match
    match_height = window.winfo_screenheight() * 0.08
    matches_labels.append(Frame(matches_scrollable, bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], height=match_height))
    matches_labels[-1].grid(row=i, column=0, pady=10, sticky="nsew")

    # 0 = home crest, 1 = away crest, 2 = home name, 3 = away name, 4 = home score, 5 = away score, 6 = match status/time
    widgets = []
    widgets.append(Label(matches_labels[-1], bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"]))
    widgets[-1].place(relx=0.075, rely=0.05, relwidth=0.25, relheight=0.6)
    widgets.append(Label(matches_labels[-1], bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"]))
    widgets[-1].place(relx=0.675, rely=0.05, relwidth=0.25, relheight=0.6)
    widgets.append(Label(matches_labels[-1], bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], font=("Segoe UI", 9), fg=SYSTEM_COLOURS[SYSTEM_MODE]["font"]))
    widgets[-1].place(relx=0, rely=0.65, relwidth=0.4, relheight=0.35)
    widgets.append(Label(matches_labels[-1], bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], font=("Segoe UI", 9), fg=SYSTEM_COLOURS[SYSTEM_MODE]["font"]))
    widgets[-1].place(relx=0.6, rely=0.65, relwidth=0.4, relheight=0.35)
    widgets.append(Label(matches_labels[-1], bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], font=("Segoe UI", 12), fg=SYSTEM_COLOURS[SYSTEM_MODE]["font"]))
    widgets[-1].place(relx=0.4, rely=0.3, relwidth=0.1, relheight=0.4)
    widgets.append(Label(matches_labels[-1], bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], font=("Segoe UI", 12), fg=SYSTEM_COLOURS[SYSTEM_MODE]["font"]))
    widgets[-1].place(relx=0.5, rely=0.3, relwidth=0.1, relheight=0.4)
    widgets.append(Label(matches_labels[-1], bg=SYSTEM_COLOURS[SYSTEM_MODE]["matches_bg"], font=("Segoe UI", 10), fg=SYSTEM_COLOURS[SYSTEM_MODE]["match_info"]))
    widgets[-1].place(relx=0.35, rely=0.7, relwidth=0.3, relheight=0.3)

    matches_widgets.append(widgets)

get_matches("", "")
#display_matches("None")

window.mainloop()