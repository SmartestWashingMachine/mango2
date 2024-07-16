def filter_dominant_bbox(speech_bboxes):
    if len(speech_bboxes) > 1:
        areas = [(s[3] - s[1]) * s(s[2] - s[0]) for s in speech_bboxes]

        best_idx = areas.index(max(areas))
        return [speech_bboxes[best_idx]]

    return speech_bboxes
