AGE : dict = {
    "min": 18,
    "max": 80,
}

GENDER : dict = {
    "Male":       50,
    "Female":     49,
    "Non-binary":  1,
}

ETHNICITY : list = [
    "North American",
    "Latin American",
    "European",
    "South Eastern Asian",
    "South Asian",
    "Middle Eastern",
    "African",
    "Oceania",
]

RELATIONSHIP_STATUS : list = [
    "Single",
    "Married",
    "Divorced",
    "Widowed",
    "In a relationship",
]

# Conditional weights per age bracket — (min_age, max_age): {status: weight}
# Based on US Census Bureau marital status data (ACS 2023)
RELATIONSHIP_WEIGHTS_BY_AGE : list[tuple] = [
    ((18, 29), {"Single": 0.60, "In a relationship": 0.25, "Married": 0.12, "Divorced": 0.02, "Widowed": 0.01}),
    ((30, 44), {"Single": 0.18, "In a relationship": 0.12, "Married": 0.55, "Divorced": 0.13, "Widowed": 0.02}),
    ((45, 64), {"Single": 0.08, "In a relationship": 0.07, "Married": 0.55, "Divorced": 0.22, "Widowed": 0.08}),
    ((65, 80), {"Single": 0.05, "In a relationship": 0.03, "Married": 0.42, "Divorced": 0.15, "Widowed": 0.35}),
]

OCCUPATION : list = [
    "Unemployed",
    "Student",
    "Retired",
    # Healthcare & Medicine
    "Doctor",
    "Nurse", 
    "Dentist", 
    "Pharmacist", 
    "Paramedic", 
    "Surgeon", 
    "Psychiatrist", 
    "Physical Therapist", 
    "Radiologist", 
    "Midwife",

    # Education
    "Teacher", 
    "Professor", 
    "School Principal", 
    "Tutor", 
    "Special Education Teacher", 
    "School Counselor", 
    "Librarian", 
    "Curriculum Designer",

    # Law & Justice
    "Lawyer", 
    "Judge", 
    "Police Officer", 
    "Detective", 
    "Prosecutor", 
    "Public Defender", 
    "Parole Officer", 
    "Forensic Analyst",

    # Military & Emergency Services
    "Soldier", 
    "Navy Officer", 
    "Firefighter", 
    "Coast Guard", 
    "Military Medic", 
    "Combat Engineer", 
    "Bomb Disposal Technician",
    "Combat Pilot",

    # Business & Finance
    "Accountant", 
    "Financial Analyst", 
    "Bank Teller", 
    "Insurance Agent", 
    "Stock Broker", 
    "Auditor", 
    "Tax Consultant", 
    "Business Owner",
    "Shopowner",
    "Salesperson",

    # Technology
    "Software Engineer", 
    "Data Scientist", 
    "IT Support", 
    "Cybersecurity Analyst", 
    "Network Engineer", 
    "UX Designer", 
    "Database Administrator",
    "QA Engineer",
    "Product Manager",
    "Project Manager",

    # Trades & Manual Labor
    "Electrician", 
    "Plumber", 
    "Carpenter", 
    "Welder", 
    "Mechanic", 
    "Construction Worker", 
    "HVAC Technician", 
    "Roofer",

    # Transportation
    "Truck Driver", 
    "Bus Driver", 
    "Taxi/Uber Driver", 
    "Airline Pilot", 
    "Train Conductor", 
    "Ship Captain", 
    "Delivery Driver",

    # Agriculture & Environment
    "Farmer", 
    "Fisherman", 
    "Forester", 
    "Agricultural Worker", 
    "Veterinarian",
    "Park Ranger", 
    "Environmental Scientist",

    # Arts & Media
    "Journalist", 
    "Photographer", 
    "Graphic Designer", 
    "Actor", 
    "Musician", 
    "Writer", 
    "Film Director", 
    "Animator",
    "Social Media Manager", 
    "Editor",
    "Publisher",
    "Model",
    "Dancer",
    "Painter",
    "Sculptor",
    "Architect",
    "Interior Designer",
    "Fashion Designer",

    # Service Industry
    "Chef", 
    "Waiter/Waitress", 
    "Bartender", 
    "Hotel Manager", 
    "Housekeeper", 
    "Retail Worker",
    "Cashier", 
    "Call Center Agent",
    "Factory Worker",
    "Warehouse Worker",
    "Fast Food Worker",
    "Prison Guard",
    "Security Guard",
    "Nanny",
    "Maid",

    # Social & Community Services
    "Social Worker", 
    "Psychologist", 
    "Counselor", 
    "Community Organizer", 
    "Non-profit Worker", 
    "Refugee Aid Worker",

    # Government & Politics
    "Politician", 
    "Civil Servant", 
    "Diplomat", 
    "Policy Analyst", 
    "Tax Inspector", 
    "Urban Planner",
    "City Council Member",

    # Religion & Spiritual Care
    "Clergy/Pastor", 
    "Rabbi", 
    "Imam", 
    "Chaplain", 
    "Social Ministry Worker",
    "Religious Educator",
    "Nun",

    # Skilled Crafts & Creative
    "Tattoo Artist", 
    "Hairdresser", 
    "Tailor", 
    "Jeweler", 
    "Potter", 
]


OCCUPATION_GROUPS : dict[str, str] = {
    # Other
    "Unemployed":               "Other",
    "Student":                  "Other",
    "Retired":                  "Other",
    # Healthcare & Medicine
    "Doctor":                   "Healthcare & Medicine",
    "Nurse":                    "Healthcare & Medicine",
    "Dentist":                  "Healthcare & Medicine",
    "Pharmacist":               "Healthcare & Medicine",
    "Paramedic":                "Healthcare & Medicine",
    "Surgeon":                  "Healthcare & Medicine",
    "Psychiatrist":             "Healthcare & Medicine",
    "Physical Therapist":       "Healthcare & Medicine",
    "Radiologist":              "Healthcare & Medicine",
    "Midwife":                  "Healthcare & Medicine",
    # Education
    "Teacher":                  "Education",
    "Professor":                "Education",
    "School Principal":         "Education",
    "Tutor":                    "Education",
    "Special Education Teacher":"Education",
    "School Counselor":         "Education",
    "Librarian":                "Education",
    "Curriculum Designer":      "Education",
    # Law & Justice
    "Lawyer":                   "Law & Justice",
    "Judge":                    "Law & Justice",
    "Police Officer":           "Law & Justice",
    "Detective":                "Law & Justice",
    "Prosecutor":               "Law & Justice",
    "Public Defender":          "Law & Justice",
    "Parole Officer":           "Law & Justice",
    "Forensic Analyst":         "Law & Justice",
    # Military & Emergency Services
    "Soldier":                  "Military & Emergency",
    "Navy Officer":             "Military & Emergency",
    "Firefighter":              "Military & Emergency",
    "Coast Guard":              "Military & Emergency",
    "Military Medic":           "Military & Emergency",
    "Combat Engineer":          "Military & Emergency",
    "Bomb Disposal Technician": "Military & Emergency",
    "Combat Pilot":             "Military & Emergency",
    # Business & Finance
    "Accountant":               "Business & Finance",
    "Financial Analyst":        "Business & Finance",
    "Bank Teller":              "Business & Finance",
    "Insurance Agent":          "Business & Finance",
    "Stock Broker":             "Business & Finance",
    "Auditor":                  "Business & Finance",
    "Tax Consultant":           "Business & Finance",
    "Business Owner":           "Business & Finance",
    "Shopowner":                "Business & Finance",
    "Salesperson":              "Business & Finance",
    # Technology
    "Software Engineer":        "Technology",
    "Data Scientist":           "Technology",
    "IT Support":               "Technology",
    "Cybersecurity Analyst":    "Technology",
    "Network Engineer":         "Technology",
    "UX Designer":              "Technology",
    "Database Administrator":   "Technology",
    "QA Engineer":              "Technology",
    "Product Manager":          "Technology",
    "Project Manager":          "Technology",
    # Trades & Manual Labor
    "Electrician":              "Trades & Manual Labor",
    "Plumber":                  "Trades & Manual Labor",
    "Carpenter":                "Trades & Manual Labor",
    "Welder":                   "Trades & Manual Labor",
    "Mechanic":                 "Trades & Manual Labor",
    "Construction Worker":      "Trades & Manual Labor",
    "HVAC Technician":          "Trades & Manual Labor",
    "Roofer":                   "Trades & Manual Labor",
    # Transportation
    "Truck Driver":             "Transportation",
    "Bus Driver":               "Transportation",
    "Taxi/Uber Driver":         "Transportation",
    "Airline Pilot":            "Transportation",
    "Train Conductor":          "Transportation",
    "Ship Captain":             "Transportation",
    "Delivery Driver":          "Transportation",
    # Agriculture & Environment
    "Farmer":                   "Agriculture & Environment",
    "Fisherman":                "Agriculture & Environment",
    "Forester":                 "Agriculture & Environment",
    "Agricultural Worker":      "Agriculture & Environment",
    "Veterinarian":             "Agriculture & Environment",
    "Park Ranger":              "Agriculture & Environment",
    "Environmental Scientist":  "Agriculture & Environment",
    # Arts & Media
    "Journalist":               "Arts & Media",
    "Photographer":             "Arts & Media",
    "Graphic Designer":         "Arts & Media",
    "Actor":                    "Arts & Media",
    "Musician":                 "Arts & Media",
    "Writer":                   "Arts & Media",
    "Film Director":            "Arts & Media",
    "Animator":                 "Arts & Media",
    "Social Media Manager":     "Arts & Media",
    "Editor":                   "Arts & Media",
    "Publisher":                "Arts & Media",
    "Model":                    "Arts & Media",
    "Dancer":                   "Arts & Media",
    "Painter":                  "Arts & Media",
    "Sculptor":                 "Arts & Media",
    "Architect":                "Arts & Media",
    "Interior Designer":        "Arts & Media",
    "Fashion Designer":         "Arts & Media",
    # Service Industry
    "Chef":                     "Service Industry",
    "Waiter/Waitress":          "Service Industry",
    "Bartender":                "Service Industry",
    "Hotel Manager":            "Service Industry",
    "Housekeeper":              "Service Industry",
    "Retail Worker":            "Service Industry",
    "Cashier":                  "Service Industry",
    "Call Center Agent":        "Service Industry",
    "Factory Worker":           "Service Industry",
    "Warehouse Worker":         "Service Industry",
    "Fast Food Worker":         "Service Industry",
    "Prison Guard":             "Service Industry",
    "Security Guard":           "Service Industry",
    "Nanny":                    "Service Industry",
    "Maid":                     "Service Industry",
    # Social & Community Services
    "Social Worker":            "Social & Community Services",
    "Psychologist":             "Social & Community Services",
    "Counselor":                "Social & Community Services",
    "Community Organizer":      "Social & Community Services",
    "Non-profit Worker":        "Social & Community Services",
    "Refugee Aid Worker":       "Social & Community Services",
    # Government & Politics
    "Politician":               "Government & Politics",
    "Civil Servant":            "Government & Politics",
    "Diplomat":                 "Government & Politics",
    "Policy Analyst":           "Government & Politics",
    "Tax Inspector":            "Government & Politics",
    "Urban Planner":            "Government & Politics",
    "City Council Member":      "Government & Politics",
    # Religion & Spiritual Care
    "Clergy/Pastor":            "Religion & Spiritual Care",
    "Rabbi":                    "Religion & Spiritual Care",
    "Imam":                     "Religion & Spiritual Care",
    "Chaplain":                 "Religion & Spiritual Care",
    "Social Ministry Worker":   "Religion & Spiritual Care",
    "Religious Educator":       "Religion & Spiritual Care",
    "Nun":                      "Religion & Spiritual Care",
    # Skilled Crafts & Creative
    "Tattoo Artist":            "Skilled Crafts & Creative",
    "Hairdresser":              "Skilled Crafts & Creative",
    "Tailor":                   "Skilled Crafts & Creative",
    "Jeweler":                  "Skilled Crafts & Creative",
    "Potter":                   "Skilled Crafts & Creative",
}


TRAUMA_TYPE : list = [
    # War-related
    "Combat",
    "Civilian in war zone",
    "Relief worker in war zone",
    "Refugee",
    "Terrorism",
    "Captivity",
    "Torture",

    # Physical violence
    "Physical abuse by caregiver (childhood)",
    "Mugging or robbery",
    "Assault",
    "Police violence",

    # Sexual and intimate partner violence
    "Rape",
    "Sexual assault",
    "Stalking",
    "Physical abuse by romantic partner",

    # Accidents and disasters
    "Life-threatening motor vehicle collision",
    "Natural disaster",
    "Man-made disaster",
    "Toxic chemical exposure",
    "Life-threatening accident",
    "Accidentally caused serious injury to another",
    "Life-threatening illness",

    # Death of loved one
    "Unexpected or traumatic death of a loved one",

    # Traumas to others
    "Child's life-threatening illness",
    "Trauma to a loved one",
    "Witnessed domestic violence (childhood)",
    "Witnessed other trauma",

    # Military and emergency services
    "Military",
    "Police",
]

PCL5 : dict = {
    "min": 33,
    "max": 80,
}

