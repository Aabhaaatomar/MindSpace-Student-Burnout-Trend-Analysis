def get_recommendations(student):
    """
    Generate personalized recommendations based on student's burnout factors.
    Accepts an object or dictionary representing student details.
    """
    if isinstance(student, dict):
        sleep = student.get('sleep_hours', 8)
        study = student.get('study_hours', 5)
        stress = student.get('stress_level', 5)
        screen = student.get('screen_time', 4)
        attendance = student.get('attendance', 90)
        fatigue = student.get('mental_fatigue', 0.5)
        physical = student.get('physical_activity', 3)
        burnout_cat = student.get('burnout_category', 'Low')
    else:
        sleep = getattr(student, 'sleep_hours', 8)
        study = getattr(student, 'study_hours', 5)
        stress = getattr(student, 'stress_level', 5)
        screen = getattr(student, 'screen_time', 4)
        attendance = getattr(student, 'attendance', 90)
        fatigue = getattr(student, 'mental_fatigue', 0.5)
        physical = getattr(student, 'physical_activity', 3)
        burnout_cat = getattr(student, 'burnout_category', 'Low')

    recs = []

    # Burnout Category Level General Warning
    if burnout_cat == 'High':
        recs.append({
            'category': 'Urgent Care',
            'title': 'Schedule an Academic Counselor Meeting',
            'text': 'Your indicators suggest severe mental fatigue and burnout. We highly recommend talking to an academic advisor or professional counselor for structural adjustment.',
            'type': 'danger',
            'icon': 'bi-exclamation-octagon'
        })
    elif burnout_cat == 'Medium':
        recs.append({
            'category': 'Preventative Action',
            'title': 'Take a Burnout Decompression Day',
            'text': 'Your indicators show moderate burnout. Consider taking a weekend completely off from academic work to recharge and connect with friends.',
            'type': 'warning',
            'icon': 'bi-lightning-charge'
        })

    # Sleep Hours Rule
    if sleep < 6.5:
        recs.append({
            'category': 'Sleep Hygiene',
            'title': 'Prioritize 7-8 Hours of Sleep',
            'text': f'You average {sleep:.1f} hours of sleep. Try to set a strict bedtime routine and avoid devices 30 minutes before sleep.',
            'type': 'danger' if sleep < 5.5 else 'warning',
            'icon': 'bi-moon-stars'
        })
    elif sleep >= 8.5 and sleep <= 10.0:
        recs.append({
            'category': 'Sleep Patterns',
            'title': 'Optimize Sleep Consistency',
            'text': f'You sleep {sleep:.1f} hours. Ensure your sleep schedule is consistent (same sleep/wake time) to boost daylight productivity.',
            'type': 'info',
            'icon': 'bi-moon'
        })

    # Screen Time Rule
    if screen > 7.0:
        recs.append({
            'category': 'Digital Wellness',
            'title': 'Reduce Non-Academic Screen Time',
            'text': f'Your average daily screen time is {screen:.1f} hours. Use app-limiters to curb social media and take 5-minute visual breaks every 30 minutes.',
            'type': 'danger' if screen > 9.0 else 'warning',
            'icon': 'bi-device-hdd'
        })

    # Stress & Fatigue Rule
    if stress > 7.0 or fatigue > 0.7:
        recs.append({
            'category': 'Mindfulness',
            'title': 'Practice Deep Breathing or Meditation',
            'text': f'Your current stress level is high ({stress:.1f}/10). Practice the 4-7-8 breathing method or spend 10 minutes in guided mindfulness daily.',
            'type': 'danger',
            'icon': 'bi-heart-pulse'
        })

    # Physical Activity Rule
    if physical < 3.0:
        recs.append({
            'category': 'Physical Well-being',
            'title': 'Integrate Light Physical Activity',
            'text': f'You record only {physical:.1f} hours of exercise per week. Aim for a 20-minute daily walk, jog, or stretch. Exercise reduces cortisol levels.',
            'type': 'warning',
            'icon': 'bi-activity'
        })
    else:
        recs.append({
            'category': 'Physical Health',
            'title': 'Maintain Current Activity Levels',
            'text': f'Great job on active exercise! Exercising {physical:.1f} hours/week is a primary buffer against cumulative academic fatigue.',
            'type': 'success',
            'icon': 'bi-check-circle'
        })

    # Study Hours vs. Balance Rule
    if study > 8.0:
        recs.append({
            'category': 'Study Balance',
            'title': 'Adopt the Pomodoro Technique',
            'text': f'Studying {study:.1f} hours/day is highly intense. Work in blocks of 50 minutes followed by 10-minute breaks to prevent cognitive fatigue.',
            'type': 'warning',
            'icon': 'bi-hourglass-split'
        })
    elif study < 2.0 and attendance < 75:
        recs.append({
            'category': 'Academic Engagement',
            'title': 'Establish a Structured Study Routine',
            'text': f'Low daily study ({study:.1f} hrs) combined with lower attendance ({attendance:.1f}%) risks academic distress. Create a daily 1-hour focus window.',
            'type': 'danger',
            'icon': 'bi-journal-check'
        })

    # Default general encouragement
    if len(recs) == 0:
        recs.append({
            'category': 'General Well-being',
            'title': 'Keep Up Your Balanced Lifestyle!',
            'text': 'Your metrics are highly balanced! You maintain good sleep, healthy screen limits, and consistent physical routines.',
            'type': 'success',
            'icon': 'bi-emoji-smile'
        })

    return recs
