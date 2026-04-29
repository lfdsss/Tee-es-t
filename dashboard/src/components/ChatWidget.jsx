import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Trash2, Bot } from 'lucide-react'
import { sendChatMessage } from '../lib/supabase'

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Bonjour ! Je suis votre assistant IA. Comment puis-je vous aider avec vos missions et propositions ?' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    const userMessage = { role: 'user', content: text }
    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setInput('')
    setLoading(true)

    try {
      // Build history from all messages (excluding the initial greeting)
      const history = updatedMessages
        .filter((_, i) => i > 0 || updatedMessages[0].role !== 'assistant')
        .map(m => ({ role: m.role, content: m.content }))

      const res = await sendChatMessage(text, history)
      const reply = res.reply || res.response || res.message || res.answer || 'Desole, je n\'ai pas pu traiter votre demande.'
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])
    } catch (err) {
      console.error('Chat error:', err)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Desole, une erreur est survenue. Verifiez votre connexion et reessayez.',
        isError: true,
      }])
    }
    setLoading(false)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function clearConversation() {
    setMessages([
      { role: 'assistant', content: 'Bonjour ! Je suis votre assistant IA. Comment puis-je vous aider avec vos missions et propositions ?' },
    ])
  }

  return (
    <>
      {/* Floating button (closed state) */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-200 group"
        >
          <MessageCircle className="w-6 h-6 group-hover:scale-110 transition-transform" strokeWidth={2} />
          {/* Pulse animation */}
          <span className="absolute inset-0 rounded-full bg-blue-600 animate-ping opacity-20" />
          {/* IA badge */}
          <span className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-violet-600 flex items-center justify-center text-[9px] font-bold text-white ring-2 ring-white">
            IA
          </span>
        </button>
      )}

      {/* Chat panel (open state) */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[calc(100vw-2rem)] sm:w-[400px] h-[500px] max-h-[calc(100vh-3rem)] bg-white rounded-2xl shadow-2xl border border-slate-200/80 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-5 py-4 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
                <Bot className="w-4.5 h-4.5 text-white" strokeWidth={2} />
              </div>
              <div>
                <p className="text-[14px] font-semibold text-white leading-none">Assistant Baptiste</p>
                <p className="text-[11px] text-blue-200 mt-0.5">En ligne</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={clearConversation}
                className="p-1.5 rounded-lg text-blue-200 hover:text-white hover:bg-white/10 transition-colors"
                title="Effacer la conversation"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-blue-200 hover:text-white hover:bg-white/10 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 bg-slate-50/50">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mr-2 mt-1">
                    <Bot className="w-3.5 h-3.5 text-blue-600" strokeWidth={2} />
                  </div>
                )}
                <div className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-[13px] leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-md'
                    : msg.isError
                    ? 'bg-red-50 text-red-700 ring-1 ring-red-200 rounded-bl-md'
                    : 'bg-white text-slate-900 shadow-sm ring-1 ring-slate-200/80 rounded-bl-md'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="flex justify-start">
                <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mr-2 mt-1">
                  <Bot className="w-3.5 h-3.5 text-blue-600" strokeWidth={2} />
                </div>
                <div className="bg-white text-slate-400 px-4 py-3 rounded-2xl rounded-bl-md shadow-sm ring-1 ring-slate-200/80 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="px-4 py-3 bg-white border-t border-slate-200 shrink-0">
            <div className="flex items-end gap-2">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ecrivez votre message..."
                rows={1}
                className="flex-1 resize-none text-[13px] py-2.5 px-3.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition-all placeholder:text-slate-400 max-h-24 overflow-y-auto"
                style={{ minHeight: '40px' }}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 disabled:cursor-not-allowed text-white flex items-center justify-center shrink-0 transition-colors shadow-sm"
              >
                <Send className="w-4 h-4" strokeWidth={2} />
              </button>
            </div>
            <p className="text-[10px] text-slate-400 mt-1.5 text-center">Shift+Entree pour un retour a la ligne</p>
          </div>
        </div>
      )}
    </>
  )
}
