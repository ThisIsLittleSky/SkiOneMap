import { ref, type Ref } from 'vue'

export function useTypewriter() {
  const typedText: Ref<string> = ref('')
  const isTyping: Ref<boolean> = ref(false)
  let timer: ReturnType<typeof setInterval> | null = null

  function start(fullText: string, speed = 60): Promise<void> {
    return new Promise((resolve) => {
      stop()
      typedText.value = ''
      isTyping.value = true
      let i = 0
      timer = setInterval(() => {
        if (i < fullText.length) {
          typedText.value += fullText[i]
          i++
        } else {
          stop()
          resolve()
        }
      }, speed)
    })
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    isTyping.value = false
  }

  function skip(fullText: string) {
    stop()
    typedText.value = fullText
    isTyping.value = false
  }

  return { typedText, isTyping, start, stop, skip }
}
