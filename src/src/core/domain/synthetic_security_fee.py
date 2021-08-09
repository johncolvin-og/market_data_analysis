import pandas as pd

def load_synthetic_security_fees(synthetic_security_leg, fee, **kwargs):
    member_type = kwargs.get('member_type')

    synth_fee = pd.merge(
        synthetic_security_leg, fee,
        on=['product_type', 'exchange', 'venue', 'security_type'], how='left')
    if member_type is not None:
        synth_fee = synth_fee.loc[synth_fee['member_type'] == member_type]
    synth_fee['net_fee'] = synth_fee['n_legs'] * synth_fee['fee']
    return synth_fee.groupby('sid').sum()
