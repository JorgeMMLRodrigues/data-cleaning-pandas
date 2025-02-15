 def extract_date_JR(cell):

    # Remove unwanted characters and strip spaces

    cleaned_cell = re.sub(r"[^0-9A-Za-z\s\-/.]", "", str(cell).strip())

    # Date formats that i want to be recognized - subject to alteration

    date_pattern = r"\b(?:\d{1,2}[-\s]?[A-Za-z]{3}[-\s]?\d{4}|" \
                   r"\d{4}-\d{2}-\d{2}|" \
                   r"[A-Za-z]{3}[-\s]?\d{1,2}[-\s]?\d{4}|" \
                   r"[A-Za-z]{3}-?\d{4}|" \
                   r"\d{4}|" \
                   r"\d{1,2}[-\s]?[A-Za-z]{3}-?\d{4}|" \
                   r"\d{4}[A-Za-z]{1,2})\b"


    # Find all matches in the cleaned string

    matches = re.findall(date_pattern, cleaned_cell)

    # Return the first match if found, otherwise return cell to later on see how to clean

    return matches[0] if matches else cell


def get_date_format_JR(date_str):

    if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        return "yyyy-mm-dd"

    if re.match(r"^\d{2}-\d{2}-\d{4}$", date_str):
        return "dd-mm-yyyy"

    if re.match(r"\d{2}[-\s][A-Za-z]{3}-\d{4}", date_str):
        return "dd-mmm-yyyy"

    if re.match(r"[A-Za-z]{3}-\d{2}-\d{4}", date_str):
        return "mmm-dd-yyyy"

    if re.match(r"\d{2}\s[A-Za-z]{3}\s\d{4}", date_str):
        return "dd-mmm-yyyy"

    if re.match(r"[A-Za-z]{3}\s\d{2}-\d{4}", date_str):
        return "mmm-dd-yyyy"

    else:
        return "Unknown Format"
    

    
def find_unknown_patterns_JR(date_series):

    unknown_values = date_series[date_series.apply(lambda cell: get_date_format_JR(str(cell)) == "Unknown Format")]

    print("Unknown Format Entries:")
    print(unknown_values.unique())


    def clean_date_special_JR(cell):

    cell = str(cell).strip()

    # Fix specific outliers

    if any(kw in cell for kw in ["World War II", "World War 2", "Woirld War II"]):
        return "01-01-1943"

    fixes = {
        '23-Decp1896': '23-Dec-1896',
        'No date': 'NaN',  #####changes made in here
        'Reported 26-Sep-t937': '26-Sep-1937',
        '10-Jul-202': '10-Jul-2020',
        '22-Jul-144': '22-Jul-1440',
        '15-Nox-2021': '15-11-2021'
    }

    return fixes.get(cell, cell)


def clean_unknown_format_JR(date_str):

    # Handle empty or non-string values.
    if not isinstance(date_str, str) or date_str.strip() == "":
        return "Invalid Date"

    date_str = date_str.strip()

    # Handle an explicit "Invalid Date" string in original column(Date).
    if date_str.lower() == "invalid date":
        return "Unknown Date"

    # List of date formats to try.
    date_formats = [
        "%Y-%m-%d",   # "2023-07-10"
        "%d-%b-%Y",   # "10-Jul-2023"
        "%b-%d-%Y",   # "Jul-10-2023"
        "%d %b %Y",   # "10 Jul 2023"
        "%b %d-%Y",   # "Jul 10-2023"
        "%d-%b %Y",   # "08-Jun 2023"
        "%d %b-%Y",   # "11 Sep-2023" (day, space, month, hyphen, year)
    ]

    # Try to parse/analyze the date using each format.
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Format as dd-mm-yyyy
            return dt.strftime("%d-%m-%Y")

        except ValueError:
            continue  # Try the next format

    # Fix dates like "20-May2015" to "20-May-2015"
    match = re.match(r"^(\d{1,2})-?([A-Za-z]{3})(\d{4})$", date_str)
    if match:
        day, month, year = match.groups()
        new_date_str = f"{day}-{month}-{year}"

        try:
            dt = datetime.strptime(new_date_str, "%d-%b-%Y")
            return dt.strftime("%d-%m-%Y")

        except ValueError:
            pass

    # Year‑only strings add January 1st.
    match = re.match(r"^(\d{4})$", date_str)
    if match:
        year = match.group(1)
        return f"16-07-{year}"

    # Handle month‑year strings like Dec-2023 by defaulting to the first day.
    match = re.match(r"^([A-Za-z]{3})-(\d{4})$", date_str)
    if match:
        month, year = match.groups()
        new_date_str = f"16-{month}-{year}"
        try:
            dt = datetime.strptime(new_date_str, "%d-%b-%Y")
            return dt.strftime("%d-%m-%Y")
        except ValueError:
            pass

    # Handle decade strings like 1990s by defaulting to January 1st.
    decade_match = re.match(r"^(\d{4})s$", date_str)
    if decade_match:
        year = decade_match.group(1)
        return f"16-07-{year}"

    # If nothing matches, return the original value.
    return date_str


def calculate_mean_day_month_JR(babyshark, date_col):

    babyshark = babyshark.copy()

    # Convert to datetime, forcing errors to Nan / new column to store this values

    babyshark[date_col] = pd.to_datetime(babyshark[date_col], format='%d-%m-%Y', errors='coerce') # 'coerce' forces to NAn

    # Drop rows where conversion failed ( only unkown will because all is clean at this point)

    babyshark = babyshark.dropna(subset=[date_col])

    # Extract day and month
    # 'dt' calls the module. 'day to lock the day in cell

    babyshark.loc[:, 'Day'] = babyshark[date_col].dt.day
    babyshark.loc[:, 'Month'] = babyshark[date_col].dt.month


    # Calculate mean values

    mean_day_JR = babyshark['Day'].mean()
    mean_month_JR = babyshark['Month'].mean()

    # Fill missing Day and Month values with the mean

    babyshark['Day'].fillna(mean_day_JR)
    babyshark['Month'].fillna(mean_month_JR)

    return mean_day_JR, mean_month_JR


def clean_species_JR(cell, species_variables_JR):

    cell = str(cell).lower().strip()

    # Check for NaN, empty string or int

    if pd.isna(cell) or str(cell).strip() == '' or not str(cell).strip():
        return 'unknown'


    if cell == 'nan':
        return 'unknown'

    # Set so no duplicated words

    found_words = set()

    for keyword in species_variables_JR:


        # makes sure to clean numbers and special charatcers in btw the letters, then removes it

        pattern_with_dots = ''.join([f'{c}[^A-Za-z0-9]*' if c.isalpha() else re.escape(c) for c in keyword])

        # Combine both patterns

        if re.search(pattern_with_dots, cell, re.IGNORECASE):
            words = set(keyword.lower().split(" "))
            found_words.update(words)

    if not found_words:
        return cell




    return ', '.join(sorted(found_words))


def species_get_nas(cell):

    cell = str(cell).strip().lower()

    cell_cleaned = re.sub(r'[^\w\s]', ' ', cell)

    # Check if the cell contains any NA-like values as whole words

    for na in species_na_values_JR:
        if re.search(r'\b' + re.escape(na) + r'\b', cell_cleaned):
            return 'unknown'
    return cell


def standardize_species_JR(cell):

    standard_map = {
    'blacktip': ['blacktip', 'blacktip shark', 'blacktip species'],
    'reef': ['reef shark', 'reef-dwelling', 'reef species'],
    'whitetip': ['whitetip', 'whitetip shark', 'whitetip species'],
    'oceanic': ['oceanic', 'oceanic species'],
    'galapagos': ['galapagos', 'galapagos shark'],
    'bull': ['bull', 'bull shark'],
    'tiger': ['tiger', 'nurse', 'grey', 'sand', 'tiger shark'],
    'white': ['great', 'great white', 'white shark'],
    'mako': ['mako', 'mako shark'],
    'basking': ['basking', 'basking shark'],
    'spotted': ['spotted', 'spotted shark'],
    'sandbar': ['sandbar', 'sandbar shark'],
    'whaler': ['whaler', 'bronze whaler'],
    'wobbegong': ['wobbegong', 'wobbegong shark'],
    'hammerhead': ['hammerhead', 'hammerhead shark'],
    'lemon': ['lemon', 'lemon shark'],
    'whitetip': ['whitetip', 'whitetip shark'],
    'galapagos': ['galapagos', 'galapagos shark'],
    'cookiecutter': ['cookiecutter', 'cookiecutter shark'],
    'porbeagle': ['porbeagle', 'porbeagle shark'],
    'angel': ['angel', 'angel shark'],
    'carpet': ['carpet', 'carpet shark'],
    'dogfish': ['dogfish', 'dogfish shark'],
    'spurdog': ['spurdog', 'spurdog shark'],
    'epaulette': ['epaulette', 'epaulette shark'],
    'goblin': ['goblin', 'goblin shark'],
    'hound': ['hound', 'hound shark'],
    'flathead': ['flathead', 'flathead shark'],
    'cat': ['cat', 'cat shark'],
    'dogfish': ['dogfish', 'dogfish shark'],
    'spotted': ['spotted', 'spotted shark'],
    'gill': ['gill', 'gill shark'],
    'thresher': ['thresher', 'thresher shark'],
    'silver': ['silver', 'silver shark'],
    'whale': ['whale', 'whale shark'],
    'saw': ['saw', 'saw shark'],
    'horn': ['horn', 'horn shark'],
    'gummy': ['gummy', 'gummy shark'],
    'broadnose': ['broadnose', 'broadnose shark'],
    }

    # Convert input to lowercase and split into words

    input_words = set(word.strip().lower() for word in cell.split(','))

    # Check if any combination of input words matches the variations


    for key, variations in standard_map.items():


        # Check each variation against the input words

        for variation in variations:

            variation_words = set(variation.lower().split())


            # If any word in the variation is found in input, return the standardized key

            if variation_words.issubset(input_words):

                return key


    # If no match is found and only 'shark' is present

    if input_words == {'shark'}:

        return 'shark, unknown'


    # If no match is found but there are other words

    return 'unknown'


def find_state(location_MO, current_state_MO):
    if current_state_MO == "UNDISCLOSED":
        for state_MO in State_l_MO['Subdivision']:
            if state_MO in str(location_MO):
                return state_MO
    return current_state_MO


def find_state(location_MO, current_state_MO):
    if current_state_MO == "UNDISCLOSED":
        for state_MO in State_l_MO['Subdivision']:
            if state_MO in str(location_MO):
                return state_MO
    return current_state_MO  # Keep original value if no match


def get_country_from_place(place_name_MO):
    # Modify query to explicitly ask about the country
    search_query_MO = f"In what country is {place_name_MO} in?"
    search_url_MO = f"https://www.googleapis.com/customsearch/v1?q={search_query_MO}&key={api_key}&cx={SEARCH_ENGINE_ID_MO}"


    try:
        response_MO = requests.get(search_url_MO)
        data2_MO = response_MO.json()

        # Check if results exist
        if "items" in data2_MO:
            for item in data2_MO["items"]:
                snippet_MO = item.get("snippet", "").upper()  # Convert to uppercase for comparison

                # Extract words and check if they match a known country
                words_MO = snippet_MO.split()
                for word_2_MO in words_MO:
                    if word_2_MO in Country_l_MO:  # Check if word is in the existing country list
                        return word_2_MO  # Return matched country

        return None  # No valid country found
    except Exception as e:
        print(f"Error for {place_name_MO}: {e}")
        return None
    

    def get_country_from_place(place_name_MO):
    # Modify query to explicitly ask about the country
    search_query_MO = f"In what country is {place_name_MO} in?"
    search_url_MO = f"https://www.googleapis.com/customsearch/v1?q={search_query_MO}&key={api_key}&cx={SEARCH_ENGINE_ID_MO}"


    try:
        response_MO = requests.get(search_url_MO)
        data2_MO = response_MO.json()

        # Check if results exist
        if "items" in data2_MO:
            for item in data2_MO["items"]:
                snippet_MO = item.get("snippet", "").upper()  # Convert to uppercase for comparison

                # Extract words and check if they match a known country
                words_MO = snippet_MO.split()
                for word_2_MO in words_MO:
                    if word_2_MO in Country_l_MO:  # Check if word is in the existing country list
                        return word_2_MO  # Return matched country

        return None  # No valid country found
    except Exception as e:
        print(f"Error for {place_name_MO}: {e}")
        return None

# Iterate through baby_shark and update 'Countries' where needed
for index_MO, row2_MO in babyshark.iterrows():
    if row2_MO["Country"] == "NO INFORMATION":  # Only search for unknown countries
        if row2_MO["Location"] == "UNDISCLOSED":  # Skip if State is 'UNDISCLOSED'
            continue

        place_name_MO = row2_MO["Location"]
        country_MO = get_country_from_place(place_name_MO)

        if country_MO:
            babyshark.at[index_MO, "Country"] = country_MO
        else:
            print(f"Could not find country for: {place_name_MO}")

        time.sleep(1)  # Sleep to avoid hitting API rate limits

print("Country lookup completed!")



def clean_type_column(babyshark):
    # Convert to lowercase and remove leading/trailing spaces
    babyshark['Type'] = babyshark['Type'].str.strip().str.lower()

    # Replace values with 'Provoked', 'Unprovoked', or 'Unverified'
    babyshark['Type'] = babyshark['Type'].apply(lambda x: 'Provoked' if x == 'provoked' else
                                          ('Unprovoked' if x == 'unprovoked' else 'Unverified'))

    return babyshark


def clean_activity_column(babyshark):
    # Convert to lowercase and remove leading/trailing spaces
    babyshark['Activity'] = babyshark['Activity'].str.strip().str.lower()

    # Define the activities that should be standardized
    activities_map = {
        'swimming': 'swimming',
        'scuba diving': 'scuba diving',
        'surfing': 'surfing',
        'spearfishing': 'spearfishing',
        'snorkelling': 'snorkelling',
        'fishing': 'fishing'
    }

    # Apply the mapping for activities
    babyshark['Activity'] = babyshark['Activity'].apply(lambda x: activities_map[x] if x in activities_map else 'water activity')

    # Replace missing values (NaN) with 'unknown'
    babyshark['Activity'].fillna('unknown', inplace=True)

    return babyshark


def clean_time(value):
    if isinstance(value, str):
        value = value.strip()

        # Remove any unnecessary spaces or extra characters
        value = re.sub(r'\s+', ' ', value)

        # Handle ranges like '1900 / 2000', '0345 - 0400', '1200 to 1400', etc.
        if '/' in value:
            return value.split('/')[0].strip()  # Take the first time in the range

        if '-' in value:
            return value.split('-')[0].strip()  # Take the first time in the range

        if 'to' in value:
            return value.split('to')[0].strip()  # Take the first time in the range

        if 'or' in value:
            return value.split('or')[0].strip()  # Take the first time in the range

        # Handle phrases with "Before" or "After"
        #if 'before' in value.lower():
            return '0600'  # Assign a reasonable time for "Before"

        #if 'after' in value.lower():
            return '1800'  # Assign a reasonable time for "After"

        # Handle specific phrases like "Midday", "Dusk", etc.
        if 'midday' in value.lower():
            return '1200'  # Midday is 1200

        if 'dusk' in value.lower():
            return '2000'  # Dusk can be 2000

        if 'night' in value.lower():
            return '2200'  # Assign a time for night

        if 'sunset' in value.lower():
            return '2000'  # Sunset can be considered around 2000

        # Handle general time cleanup
        value = value.replace(' ', '').replace('pm', '').replace('am', '')

        # Convert to 4-digit format (HHMM)
        try:
            if len(value) == 4 and value.isdigit():  # If it's already in HHMM format
                return value
            if len(value) == 3 and value.isdigit():  # Handle cases like '900' (convert to '0900')
                return f"0{value}"
            if len(value) == 2 and value.isdigit():  # Handle cases like '30' (convert to '0030')
                return f"00{value}"
        except ValueError:
            return None

    return None  # In case no valid time is found


def categorize_time(time):
    # Check if time is valid (not None or invalid string)
    if pd.isna(time) or time in ['bef', '2 bef', 'Bef','S']:
        return None

    # Handle time format
    try:
        # Convert to string if needed, then parse time as string (HHMM format)
        time_str = str(time).zfill(4)  # Ensure 4 digits (e.g., 0600 for 6 AM)
        hour = int(time_str[:2])  # Extract hour (first two digits)
        minute = int(time_str[2:])  # Extract minutes (last two digits)

        # Assign to categories based on the time
        if 6 <= hour < 12:  # Morning
            return 'Morning'
        elif 12 <= hour < 18:  # Afternoon
            return 'Afternoon'
        elif 18 <= hour < 21:  # Evening
            return 'Evening'
        else:  # Night (21:00 - 05:59)
            return 'Night'
    except ValueError:
        return None
