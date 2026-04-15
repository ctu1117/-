export const EMOTION_MAP = {
  'Happy :)': {
    icon: '😊',
    label: '开心',
    longLabel: '开心愉悦',
    chipStyle: 'emotion-happy',
    color: '#f7c948',
    score: 5,
  },
  'Angry >_<': {
    icon: '😠',
    label: '生气',
    longLabel: '愤怒烦躁',
    chipStyle: 'emotion-angry',
    color: '#f77c6a',
    score: 2,
  },
  'Sad  :(': {
    icon: '😢',
    label: '难过',
    longLabel: '低落难过',
    chipStyle: 'emotion-sad',
    color: '#6ea8f7',
    score: 1,
  },
  'Surprise!': {
    icon: '😮',
    label: '惊讶',
    longLabel: '惊讶意外',
    chipStyle: 'emotion-surprise',
    color: '#a78bfa',
    score: 4,
  },
  'Neutral :|': {
    icon: '🙂',
    label: '平静',
    longLabel: '平静稳定',
    chipStyle: 'emotion-neutral',
    color: '#5de0e6',
    score: 3,
  },
  'No Face': {
    icon: '🙈',
    label: '未检测到人脸',
    longLabel: '未检测到人脸',
    chipStyle: 'emotion-neutral',
    color: '#9ca3af',
    score: null,
  },
}

export const JOURNAL_EMOTIONS = ['Happy :)', 'Neutral :|', 'Sad  :(', 'Angry >_<', 'Surprise!']

export function getEmotionMeta(emotion) {
  return EMOTION_MAP[emotion] ?? EMOTION_MAP['Neutral :|']
}
