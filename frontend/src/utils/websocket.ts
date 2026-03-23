export function connectWebSocket(
  url: string,
  onMessage: (data: any) => void,
  onOpen?: () => void,
  onClose?: () => void
): WebSocket {
  const ws = new WebSocket(url)

  ws.onopen = () => {
    console.log('WebSocket connected')
    onOpen?.()
  }

  ws.onmessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data)
      onMessage(data)
    } catch {
      console.warn('Failed to parse WebSocket message:', event.data)
    }
  }

  ws.onclose = () => {
    console.log('WebSocket disconnected')
    onClose?.()
    setTimeout(() => connectWebSocket(url, onMessage, onOpen, onClose), 5000)
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }

  return ws
}
