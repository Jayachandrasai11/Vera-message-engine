
from app.engine.decision import decide_action
from app.engine.composer import compose_message

# Test recall_due
ctx = {'merchant_id': 'm_001', 'name': 'Dr. Meera', 'rating': 4.2, 'offers': [], 'category': {'slug': 'dentists'}}
trig = {'type': 'recall_due'}
r = decide_action(ctx, trig)
print('recall_due action:', r['selected_action'])

# Test research
trig = {'type': 'research'}
r = decide_action(ctx, trig)
print('research action:', r['selected_action'])

