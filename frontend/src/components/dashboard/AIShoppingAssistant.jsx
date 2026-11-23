
import { useState } from 'react'
import { Bot, Send, Sparkles, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { sendAIMessage } from '../../api/aiApi'
import { getErrorMessage } from '../../api/axios'
import remarkGfm from 'remark-gfm'

const suggestions = [
  'What should I buy this week?',
  'How can I save money on groceries?',
  'Which items should I prioritise?',
  'Suggest a shopping list within ₹2,000.',
]

export default function AIShoppingAssistant() {
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSend = async (text = question) => {
    const userQuestion = text.trim()

    if (!userQuestion || loading) return

    const previousMessages = messages
    const history = previousMessages
  .slice(-10)
  .filter(
    (message) =>
      ['user', 'assistant'].includes(message.role) &&
      typeof message.content === 'string' &&
      message.content.length <= 2000
  )
  .map(({ role, content }) => ({
    role,
    content,
  }))
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: userQuestion },
    ])
    setQuestion('')
    setLoading(true)
    setError('')

    try {
      const result = await sendAIMessage(userQuestion, history)

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: result.answer },
      ])
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to get an AI response.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card overflow-hidden">
      <div className="flex items-center gap-3 border-b border-slate-100 px-5 py-4">
        <div className="rounded-xl bg-violet-100 p-2 text-violet-700">
          <Bot className="h-6 w-6" />
        </div>
        <div>
          <h2 className="font-semibold text-slate-900">
            AI Shopping Assistant
          </h2>
          <p className="text-xs text-slate-500">
            Your personal grocery planning assistant
          </p>
        </div>
      </div>

      <div className="max-h-[450px] min-h-[220px] space-y-4 overflow-y-auto p-5">
        {!messages.length && (
          <div className="py-4 text-center">
            <Sparkles className="mx-auto mb-3 h-8 w-8 text-violet-500" />
            <p className="font-medium text-slate-800">
              How can I help with your groceries?
            </p>
            <p className="mt-1 text-sm text-slate-500">
              Ask me about shopping, budget or inventory.
            </p>

            <div className="mt-5 flex flex-wrap justify-center gap-2">
              {suggestions.map((item) => (
                <button
                  key={item}
                  type="button"
                  disabled={loading}
                  onClick={() => handleSend(item)}
                  className="rounded-full border border-slate-200 px-3 py-2 text-xs text-slate-600 hover:border-violet-300 hover:bg-violet-50"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex gap-2 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.role === 'assistant' && (
              <Bot className="mt-1 h-5 w-5 shrink-0 text-violet-600" />
            )}

            <div
              className={`max-w-[85%] rounded-xl px-4 py-3 text-sm ${
                message.role === 'user'
                  ? 'bg-violet-600 text-white'
                  : 'bg-slate-100 text-slate-800'
              }`}
            >
              {message.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
  {message.content}
</ReactMarkdown>
                </div>
              ) : (
                message.content
              )}
            </div>

            {message.role === 'user' && (
              <User className="mt-1 h-5 w-5 shrink-0 text-slate-500" />
            )}
          </div>
        ))}

        {loading && (
          <p className="text-sm text-slate-500">
            AI is thinking...
          </p>
        )}

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
      </div>

      <form
        className="flex gap-2 border-t border-slate-100 p-4"
        onSubmit={(event) => {
          event.preventDefault()
          handleSend()
        }}
      >
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about your groceries..."
          maxLength={1000}
          disabled={loading}
          className="input flex-1"
        />

        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="btn btn-primary"
        >
          <Send className="h-4 w-4" />
          Send
        </button>
      </form>
    </section>
  )
}
