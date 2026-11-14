"""Frozen stored-order extraction; no score/label-based choice or fallback."""
def extract_last(row, method):
    if method == 'PAIR':
        streams = row['streams']
        entry = streams[-1][-1]
        position = dict(stored_flow_position_1based=len(streams),
                        stored_entry_position_1based=len(streams[-1]))
    elif method == 'TAP':
        logs = row['source_logs']
        entry = logs[-1]
        position = dict(stored_log_position_1based=len(logs),
                        tree_node_id=None, absolute_depth=None)
    else:
        raise ValueError(method)
    prompt = entry['adv_prompt']
    assert isinstance(prompt, str) and prompt
    return prompt, position
