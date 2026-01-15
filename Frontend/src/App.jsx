import { motion } from 'framer-motion';
import ChatWindow from './components/ChatWindow';
import AvatarPlaceholder from './components/AvatarPlaceholder';
import { useChat } from './hooks/useChat';

/**
 * App - Main application component
 * 
 * Editorial-style layout with:
 * - Left section: AI Avatar placeholder
 * - Right section: Chat interface
 * 
 * Designed for desktop-first, mobile-friendly experience.
 */

function App() {
  const { messages, isLoading, sendMessage } = useChat();

  return (
    <div className="min-h-screen bg-cream relative overflow-hidden">
      {/* Subtle background texture */}
      <div className="absolute inset-0 noise-texture pointer-events-none" />

      {/* Decorative background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Top-right gradient orb */}
        <motion.div
          className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-accent-soft/30 blur-3xl"
          animate={{
            scale: [1, 1.1, 1],
            x: [0, 20, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        {/* Bottom-left gradient orb */}
        <motion.div
          className="absolute -bottom-48 -left-48 w-[30rem] h-[30rem] rounded-full bg-sage-soft/40 blur-3xl"
          animate={{
            scale: [1, 1.15, 1],
            y: [0, -30, 0],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 2,
          }}
        />
      </div>

      {/* Main content */}
      <div className="relative z-10 min-h-screen flex flex-col lg:flex-row">

        {/* Left section - Avatar area (hidden on mobile, visible on lg+) */}
        <motion.aside
          className="hidden lg:flex lg:w-2/5 xl:w-1/2 min-h-screen bg-gradient-to-br from-linen/50 to-transparent border-r border-stone/10"
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <AvatarPlaceholder />
        </motion.aside>

        {/* Right section - Chat interface */}
        <motion.main
          className="flex-1 lg:w-3/5 xl:w-1/2 min-h-screen flex flex-col"
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
        >
          {/* Mobile header with condensed avatar hint */}
          <motion.div
            className="lg:hidden flex items-center gap-4 px-6 py-4 border-b border-stone/20 bg-white/50 backdrop-blur-sm"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            {/* Mini avatar indicator */}
            <div className="w-12 h-12 rounded-[35%_65%_60%_40%/50%_40%_60%_50%] bg-gradient-to-br from-accent-soft to-sage-soft flex items-center justify-center border border-stone/20">
              <svg
                className="w-6 h-6 text-slate"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-medium text-ink">AI Assistant</h1>
              <p className="text-xs text-mist">Ready to help</p>
            </div>
          </motion.div>

          {/* Chat window */}
          <div className="flex-1 overflow-hidden">
            <ChatWindow
              messages={messages}
              isLoading={isLoading}
              onSendMessage={sendMessage}
            />
          </div>
        </motion.main>
      </div>

      {/* Decorative corner accents */}
      <div className="absolute top-6 left-6 w-24 h-px bg-gradient-to-r from-stone/40 to-transparent pointer-events-none hidden lg:block" />
      <div className="absolute top-6 left-6 w-px h-24 bg-gradient-to-b from-stone/40 to-transparent pointer-events-none hidden lg:block" />
      <div className="absolute bottom-6 right-6 w-24 h-px bg-gradient-to-l from-stone/40 to-transparent pointer-events-none hidden lg:block" />
      <div className="absolute bottom-6 right-6 w-px h-24 bg-gradient-to-t from-stone/40 to-transparent pointer-events-none hidden lg:block" />
    </div>
  );
}

export default App;
