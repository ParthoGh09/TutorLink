"""Shared choice lists for the tuition screens (09, 10, 11).

NOTE: SUBJECTS is a plain list for now. When the admin ``Subject`` model
(Subject.add_subject() on the Admin Dashboard) exists, swap this for a query.
"""

SUBJECTS = [
    "Mathematics",
    "Higher Math",
    "Physics",
    "Chemistry",
    "Biology",
    "English",
    "ICT",
    "Bangla",
    "Accounting",
    "Economics",
]

CLASS_LEVELS = (
    [f"Class {n}" for n in range(1, 11)]
    + ["HSC 1st Year", "HSC 2nd Year", "Admission Prep", "University"]
)

DAYS = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]

TIME_SLOTS = [
    "8:00 AM – 10:00 AM",
    "10:00 AM – 12:00 PM",
    "3:00 PM – 5:00 PM",
    "4:00 PM – 6:00 PM",
    "5:00 PM – 7:00 PM",
    "6:00 PM – 8:00 PM",
    "7:00 PM – 9:00 PM",
    "8:00 PM – 10:00 PM",
]

# Division -> District -> [Areas]. Only the area is ever public (privacy promise).
LOCATIONS = {
    "Dhaka": {
        "Dhaka": [
            "Dhanmondi", "Mirpur", "Kalabagan", "Shankar", "Mohammadpur",
            "Uttara", "Gulshan", "Banani", "Farmgate", "Motijheel", "Badda",
        ],
        "Gazipur": ["Tongi", "Joydebpur", "Kaliakoir"],
        "Narayanganj": ["Narayanganj Sadar", "Fatullah", "Siddhirganj"],
    },
    "Chattogram": {
        "Chattogram": ["Agrabad", "Khulshi", "Pahartali", "Nasirabad", "GEC Circle"],
        "Cox's Bazar": ["Cox's Bazar Sadar"],
    },
    "Rajshahi": {"Rajshahi": ["Boalia", "Shaheb Bazar", "Motihar"]},
    "Khulna": {"Khulna": ["Sonadanga", "Khalishpur", "Daulatpur"]},
    "Sylhet": {"Sylhet": ["Zindabazar", "Ambarkhana", "Subid Bazar"]},
    "Barishal": {"Barishal": ["Barishal Sadar", "Nathullabad"]},
    "Rangpur": {"Rangpur": ["Rangpur Sadar", "Jahaj Company More"]},
    "Mymensingh": {"Mymensingh": ["Mymensingh Sadar", "Ganginarpar"]},
}
