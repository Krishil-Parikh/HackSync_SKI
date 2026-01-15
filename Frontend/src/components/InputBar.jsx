import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Send, MicOff } from 'lucide-react';

/**
 * InputBar - Message input section
 * 
 * Features:
 * - Text input for typing messages
 * - Voice input button (UI-only placeholder)
 * - Send button with interaction feedback
 * 
 * TODO: Connect to speech-to-text API for voice input
 * TODO: Add typing indicators when AI is processing
 */

const InputBar = ({ onSendMessage, isLoading }) => {
    const [inputValue, setInputValue] = useState('');
    const [isListening, setIsListening] = useState(false);
    const inputRef = useRef(null);

    // Focus input on mount
    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    // Handle form submission
    const handleSubmit = (e) => {
        e.preventDefault();
        if (inputValue.trim() && !isLoading) {
            onSendMessage(inputValue);
            setInputValue('');
        }
    };

    // Handle voice input toggle (UI only)
    // TODO: Implement actual speech recognition
    const handleVoiceToggle = () => {
        setIsListening(!isListening);

        // TODO: Replace with actual speech recognition implementation
        // Example integration:
        // if (!isListening) {
        //   const recognition = new webkitSpeechRecognition();
        //   recognition.continuous = false;
        //   recognition.interimResults = true;
        //   recognition.onresult = (event) => {
        //     const transcript = event.results[0][0].transcript;
        //     setInputValue(transcript);
        //   };
        //   recognition.start();
        // } else {
        //   recognition.stop();
        // }

        // Auto-reset after 3 seconds (demo behavior)
        if (!isListening) {
            setTimeout(() => setIsListening(false), 3000);
        }
    };

    // Handle keyboard shortcuts
    const handleKeyDown = (e) => {
        // Submit on Enter (without Shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const canSend = inputValue.trim() && !isLoading;

    return (
        <motion.form
            onSubmit={handleSubmit}
            className="relative"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
            {/* Main input container */}
            <div className="relative flex items-center gap-2 p-2 bg-white/70 backdrop-blur-xl rounded-2xl border border-stone/20 shadow-lg shadow-shadow">
                {/* Voice input button */}
                <motion.button
                    type="button"
                    onClick={handleVoiceToggle}
                    className={`
            relative flex-shrink-0 p-3 rounded-xl transition-colors duration-200
            ${isListening
                            ? 'bg-accent text-white'
                            : 'bg-linen text-slate hover:bg-sand hover:text-charcoal'
                        }
          `}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    aria-label={isListening ? 'Stop listening' : 'Start voice input'}
                >
                    <AnimatePresence mode="wait">
                        {isListening ? (
                            <motion.div
                                key="listening"
                                initial={{ scale: 0, rotate: -180 }}
                                animate={{ scale: 1, rotate: 0 }}
                                exit={{ scale: 0, rotate: 180 }}
                                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                            >
                                <MicOff className="w-5 h-5" />
                            </motion.div>
                        ) : (
                            <motion.div
                                key="idle"
                                initial={{ scale: 0, rotate: 180 }}
                                animate={{ scale: 1, rotate: 0 }}
                                exit={{ scale: 0, rotate: -180 }}
                                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                            >
                                <Mic className="w-5 h-5" />
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Listening indicator pulse */}
                    {isListening && (
                        <motion.div
                            className="absolute inset-0 rounded-xl bg-accent"
                            initial={{ opacity: 0.5 }}
                            animate={{
                                opacity: [0.5, 0.2, 0.5],
                                scale: [1, 1.2, 1],
                            }}
                            transition={{
                                duration: 1.5,
                                repeat: Infinity,
                                ease: "easeInOut",
                            }}
                            style={{ zIndex: -1 }}
                        />
                    )}
                </motion.button>

                {/* Text input */}
                <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={isListening ? "Listening..." : "Type your message..."}
                    disabled={isLoading}
                    className={`
            flex-1 px-4 py-3 bg-transparent text-ink placeholder-mist
            text-[15px] font-light tracking-wide
            focus:outline-none
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
                    aria-label="Message input"
                />

                {/* Send button */}
                <motion.button
                    type="submit"
                    disabled={!canSend}
                    className={`
            flex-shrink-0 p-3 rounded-xl transition-all duration-200
            ${canSend
                            ? 'bg-gradient-to-br from-accent to-accent-deep text-white shadow-md hover:shadow-lg'
                            : 'bg-sand text-mist cursor-not-allowed'
                        }
          `}
                    whileHover={canSend ? { scale: 1.05 } : {}}
                    whileTap={canSend ? { scale: 0.95 } : {}}
                    aria-label="Send message"
                >
                    <AnimatePresence mode="wait">
                        {isLoading ? (
                            <motion.div
                                key="loading"
                                className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
                                animate={{ rotate: 360 }}
                                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            />
                        ) : (
                            <motion.div
                                key="send"
                                initial={{ scale: 0.8, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.8, opacity: 0 }}
                                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                            >
                                <Send className="w-5 h-5" />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.button>
            </div>

            {/* Helper text */}
            <motion.p
                className="mt-2 text-center text-xs text-mist font-light"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
            >
                Press <kbd className="px-1.5 py-0.5 bg-linen rounded text-slate">Enter</kbd> to send
            </motion.p>
        </motion.form>
    );
};

export default InputBar;
