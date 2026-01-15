import { motion } from 'framer-motion';

/**
 * MessageBubble - Individual chat message display
 * 
 * Renders user and AI messages with distinct styling.
 * Uses Framer Motion for smooth entry animations.
 */

const MessageBubble = ({ message, isLatest }) => {
    const isUser = message.role === 'user';
    const isError = message.isError;

    // Format timestamp
    const formatTime = (timestamp) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    };

    // Animation variants
    const bubbleVariants = {
        hidden: {
            opacity: 0,
            y: 20,
            scale: 0.95,
        },
        visible: {
            opacity: 1,
            y: 0,
            scale: 1,
            transition: {
                type: "spring",
                stiffness: 300,
                damping: 25,
                duration: 0.4,
            }
        },
    };

    return (
        <motion.div
            className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
            variants={bubbleVariants}
            initial="hidden"
            animate="visible"
            layout
        >
            <div className={`flex flex-col max-w-[75%] md:max-w-[65%] ${isUser ? 'items-end' : 'items-start'}`}>
                {/* Message bubble */}
                <motion.div
                    className={`
            relative px-5 py-3.5 rounded-2xl
            ${isUser
                            ? 'bg-gradient-to-br from-accent to-accent-deep text-white rounded-br-md'
                            : isError
                                ? 'bg-red-50 text-red-800 border border-red-200 rounded-bl-md'
                                : 'bg-white/80 backdrop-blur-sm text-charcoal border border-stone/20 rounded-bl-md shadow-sm'
                        }
          `}
                    whileHover={{ scale: 1.01 }}
                    transition={{ type: "spring", stiffness: 400, damping: 25 }}
                >
                    {/* Message content */}
                    <p className={`
            text-[15px] leading-relaxed font-light
            ${isUser ? 'text-white/95' : ''}
          `}>
                        {message.content}
                    </p>

                    {/* Subtle gradient overlay for user messages */}
                    {isUser && (
                        <div className="absolute inset-0 rounded-2xl rounded-br-md bg-gradient-to-t from-black/5 to-transparent pointer-events-none" />
                    )}
                </motion.div>

                {/* Timestamp */}
                <motion.span
                    className={`
            mt-1.5 text-xs font-light tracking-wide
            ${isUser ? 'text-mist mr-1' : 'text-mist ml-1'}
          `}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                >
                    {formatTime(message.timestamp)}
                </motion.span>
            </div>
        </motion.div>
    );
};

export default MessageBubble;
