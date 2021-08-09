import pandas as pd
from src.pcap_location_params import PCapLocationParams

def load_security(channel, date):
    security = pd.read_feather(PCapLocationParams(channel).feather_file_path('security', date=date))
    return security
