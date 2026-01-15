import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MessageBubble from './MessageBubble';
import InputBar from './InputBar';

/**
 * ChatWindow - Main chat interface container
 * 
 * Orchestrates message display and input handling.
 * Designed for clean separation of concerns and easy extension.
 */

const ChatWindow = ({ messages, isLoading, onSendMessage }) => {
    const messagesEndRef = useRef(null);
    const messagesContainerRef = useRef(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({
            behavior: 'smooth',
            block: 'end',
        });
    }, [messages]);

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <motion.header
                className="flex-shrink-0 px-6 py-5 border-b border-stone/20"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-medium text-ink tracking-tight">
                            Conversation
                        </h1>
                        <p className="text-sm text-mist font-light mt-0.5">
                            with AI Assistant
                        </p>
                    </div>

                    {/* Status indicator */}
                    <div className="flex items-center gap-2">
                        <motion.div
                            className={`w-2 h-2 rounded-full ${isLoading ? 'bg-accent' : 'bg-sage'}`}
                            animate={isLoading ? {
                                scale: [1, 1.3, 1],
                                opacity: [1, 0.5, 1],
                            } : {}}
                            transition={{
                                duration: 1,
                                repeat: Infinity,
                                ease: "easeInOut",
                            }}
                        />
                        <span className="text-xs text-mist font-light">
                            {isLoading ? 'Thinking...' : 'Online'}
                        </span>
                    </div>
                </div>
            </motion.header>

            {/* Messages area */}
            <div
                ref={messagesContainerRef}
                className="flex-1 overflow-y-auto px-6 py-6 scrollbar-elegant"
            >
                <AnimatePresence mode="popLayout">
                    {messages.map((message, index) => (
                        <MessageBubble
                            key={message.id}
                            message={message}
                            isLatest={index === messages.length - 1}
                        />
                    ))}
                </AnimatePresence>

                {/* Typing indicator when loading */}
                <AnimatePresence>
                    {isLoading && (
                        <motion.div
                            className="flex justify-start mb-4"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.3 }}
                        >
                            <div className="px-5 py-4 bg-white/80 backdrop-blur-sm rounded-2xl rounded-bl-md border border-stone/20 shadow-sm">
                                <div className="flex items-center gap-1.5">
                                    {[0, 1, 2].map((i) => (
                                        <motion.div
                                            key={i}
                                            className="w-2 h-2 rounded-full bg-accent/60"
                                            animate={{
                                                y: [0, -6, 0],
                                                opacity: [0.4, 1, 0.4],
                                            }}
                                            transition={{
                                                duration: 0.8,
                                                repeat: Infinity,
                                                delay: i * 0.15,
                                                ease: "easeInOut",
                                            }}
                                        />
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Scroll anchor */}
                <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            <div className="flex-shrink-0 px-6 pb-6 pt-2">
                <InputBar
                    onSendMessage={onSendMessage}
                    isLoading={isLoading}
                />
            </div>
        </div>
    );
};

export default ChatWindow;
