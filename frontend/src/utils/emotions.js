export const EMOTION_MAP = {
  'Happy :)': {
    icon: '😊',
    label: '开心',
    longLabel: '开心 Happy',
    chipStyle: 'emotion-happy',
  },
  'Angry >_<': {
    icon: '😠',
    label: '生气',
    longLabel: '生气 Angry',
    chipStyle: 'emotion-angry',
  },
  'Sad  :(': {
    icon: '😔',
    label: '难过',
    longLabel: '难过 Sad',
    chipStyle: 'emotion-sad',
  },
  'Surprise!': {
    icon: '😮',
    label: '惊喜',
    longLabel: '惊喜 Surprise',
    chipStyle: 'emotion-surprise',
  },
  'Neutral :|': {
    icon: '😌',
    label: '平静',
    longLabel: '平静 Neutral',
    chipStyle: 'emotion-neutral',
  },
  'No Face': {
    icon: '🙂',
    label: '未知',
    longLabel: '未知',
    chipStyle: 'emotion-neutral',
  },
}

export const JOURNAL_EMOTIONS = ['Happy :)', 'Neutral :|', 'Sad  :(', 'Angry >_<', 'Surprise!']

export function getEmotionMeta(emotion) {
  return EMOTION_MAP[emotion] ?? EMOTION_MAP['Neutral :|']
}
