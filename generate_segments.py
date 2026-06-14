#!/usr/bin/env python3
import json
import os

output_dir = 'output'
segments_file = os.path.join(output_dir, 'lantern_v6_segments.json')

highlights = [
    {'start': 50.0, 'end': 53.0, 'text': 'WAIT FOR IT...', 'reason': 'motion'},
    {'start': 120.0, 'end': 124.0, 'text': 'CLUTCH MOMENT', 'reason': 'audio_peak'},
    {'start': 200.0, 'end': 203.0, 'text': 'NO WAY', 'reason': 'motion'},
    {'start': 300.0, 'end': 304.0, 'text': 'INSANE PLAY', 'reason': 'audio_peak'},
    {'start': 400.0, 'end': 403.0, 'text': 'THIS IS CRAZY', 'reason': 'motion'},
    {'start': 500.0, 'end': 504.0, 'text': 'GG EASY', 'reason': 'audio_peak'},
    {'start': 600.0, 'end': 603.0, 'text': 'ONE SHOT', 'reason': 'motion'},
    {'start': 700.0, 'end': 704.0, 'text': 'UNREAL', 'reason': 'audio_peak'},
]

segments_data = {
    'total_segments': len(highlights),
    'total_duration': sum(h['end'] - h['start'] for h in highlights),
    'segments': [
        {
            'index': i,
            'start': h['start'],
            'end': h['end'],
            'duration': h['end'] - h['start'],
            'caption': h['text'],
            'reason': h['reason']
        }
        for i, h in enumerate(highlights, 1)
    ]
}

with open(segments_file, 'w') as f:
    json.dump(segments_data, f, indent=2)

print(f'Created: {segments_file}')
print(f'Total segments: {segments_data["total_segments"]}')
print(f'Total duration: {segments_data["total_duration"]:.1f}s')
